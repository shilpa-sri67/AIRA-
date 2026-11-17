import os
import asyncio
import audioop

from pathlib import Path
from datetime import datetime

import sounddevice as sd

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "gemini-3.5-transcribe-live"

MIC_DEVICE = 1

INPUT_RATE = 44100
OUTPUT_RATE = 16000

CHANNELS = 1
BLOCK_SIZE = 4410

QUEUE_SIZE = 200

RECONNECT_DELAY = 2
MAX_RECONNECT_DELAY = 30


# ==================================================
# LOAD API KEY
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("Gemini API key not found!")


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(api_key=API_KEY)

config = types.LiveConnectConfig(

    response_modalities=["TEXT"],

    input_audio_transcription=types.AudioTranscriptionConfig(
        language_codes=["en-IN"],
        mode="VERBATIM"
    )
)


# ==================================================
# AUDIO QUEUE
# ==================================================

def enqueue_audio(audio_queue, audio_data):

    # Prevent unlimited audio accumulation.

    if audio_queue.full():

        try:
            audio_queue.get_nowait()
            audio_queue.task_done()

        except asyncio.QueueEmpty:
            pass

    audio_queue.put_nowait(audio_data)


# ==================================================
# MICROPHONE CAPTURE
# ==================================================

def create_microphone_stream(audio_queue, loop):

    def microphone_callback(indata, frames, time_info, status):

        if status:
            print("\nMicrophone warning:", status)

        audio_data = bytes(indata)

        try:
            loop.call_soon_threadsafe(
                enqueue_audio,
                audio_queue,
                audio_data
            )

        except RuntimeError:
            pass

    stream = sd.RawInputStream(

        device=MIC_DEVICE,

        samplerate=INPUT_RATE,

        channels=CHANNELS,

        dtype="int16",

        blocksize=BLOCK_SIZE,

        callback=microphone_callback
    )

    return stream


# ==================================================
# AUDIO SENDER
# ==================================================

async def microphone_sender(session, audio_queue):

    resample_state = None

    print("\nGemini audio sender started.")

    while True:

        audio_data = await audio_queue.get()

        try:

            converted_audio, resample_state = audioop.ratecv(

                audio_data,

                2,

                CHANNELS,

                INPUT_RATE,

                OUTPUT_RATE,

                resample_state
            )

            if not converted_audio:
                continue

            await session.send_realtime_input(

                audio=types.Blob(

                    data=converted_audio,

                    mime_type="audio/pcm;rate=16000"
                )
            )

        finally:

            audio_queue.task_done()


# ==================================================
# TRANSCRIPTION RECEIVER
# ==================================================

async def transcription_receiver(session):

    print("Gemini transcription receiver started.")

    async for response in session.receive():

        # Check whether Gemini is about to terminate
        # the current connection.

        if response.go_away is not None:

            print("\nGemini is closing this connection.")

            print(
                "Time remaining:",
                response.go_away.time_left
            )

            return

        content = response.server_content

        if content is None:
            continue

        transcription = content.input_transcription

        if transcription and transcription.text:

            text = transcription.text.strip()

            if text:

                timestamp = datetime.now().strftime(
                    "%H:%M:%S"
                )

                print("\n" + "-" * 55)

                print(
                    f"[{timestamp}] YOU: {text}"
                )

                print("-" * 55)

                print("\nAIRA is listening...")


# ==================================================
# RUN ONE GEMINI SESSION
# ==================================================

async def run_gemini_session(audio_queue):

    async with client.aio.live.connect(

        model=MODEL,

        config=config

    ) as session:

        print("\nGemini connected successfully!")

        print("Starting transcription...")

        sender_task = asyncio.create_task(

            microphone_sender(
                session,
                audio_queue
            )

        )

        receiver_task = asyncio.create_task(

            transcription_receiver(session)

        )

        tasks = [sender_task, receiver_task]

        try:

            done, pending = await asyncio.wait(

                tasks,

                return_when=asyncio.FIRST_COMPLETED

            )

            # Stop the other task when either
            # side terminates.

            for task in pending:
                task.cancel()

            await asyncio.gather(
                *pending,
                return_exceptions=True
            )

            # Propagate actual sender/receiver errors.

            for task in done:

                exception = task.exception()

                if exception:
                    raise exception

            # A normal receiver exit also means
            # this session needs replacing.

            raise ConnectionError(
                "Gemini session ended."
            )

        finally:

            for task in tasks:

                if not task.done():
                    task.cancel()

            await asyncio.gather(
                *tasks,
                return_exceptions=True
            )


# ==================================================
# AUTOMATIC RECONNECTION
# ==================================================

async def connection_manager(audio_queue):

    retry_delay = RECONNECT_DELAY

    while True:

        try:

            print("\nConnecting to Gemini Live...")

            await run_gemini_session(audio_queue)

            retry_delay = RECONNECT_DELAY

        except asyncio.CancelledError:

            raise

        except Exception as error:

            print("\n" + "=" * 55)

            print("GEMINI CONNECTION INTERRUPTED")

            print("Error:", type(error).__name__)

            print("Details:", error)

            print(
                f"\nReconnecting in {retry_delay} seconds..."
            )

            print("=" * 55)

            await asyncio.sleep(retry_delay)

            retry_delay = min(
                retry_delay * 2,
                MAX_RECONNECT_DELAY
            )


# ==================================================
# MAIN
# ==================================================

async def main():

    audio_queue = asyncio.Queue(
        maxsize=QUEUE_SIZE
    )

    loop = asyncio.get_running_loop()

    print("\n====================================")
    print("       AIRA LIVE TRANSCRIPTION")
    print("====================================")

    print("Model:", MODEL)

    print("Microphone:", MIC_DEVICE)

    print("Input:", INPUT_RATE, "Hz")

    print("Output:", OUTPUT_RATE, "Hz")

    print("\nInitializing microphone...")

    stream = create_microphone_stream(
        audio_queue,
        loop
    )

    try:

        with stream:

            print("\nMicrophone ready.")

            print("AIRA is listening...\n")

            await connection_manager(audio_queue)

    finally:

        if stream.active:
            stream.stop()

        stream.close()


# ==================================================
# START AIRA
# ==================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\n\nAIRA stopped by user.")

    except Exception as error:

        print("\nAIRA FATAL ERROR")

        print("Type:", type(error).__name__)

        print("Details:", error)