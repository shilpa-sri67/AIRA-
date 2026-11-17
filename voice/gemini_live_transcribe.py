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

# Microphone's native sample rate
INPUT_RATE = 44100

# Gemini's required audio sample rate
OUTPUT_RATE = 16000

CHANNELS = 1
BLOCK_SIZE = 882  # 20 milliseconds at 44.1 kHz

QUEUE_SIZE = 200


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
# AUDIO STREAMING
# ==================================================

async def microphone_sender(session, audio_queue):

    loop = asyncio.get_running_loop()

    def microphone_callback(indata, frames, time_info, status):

        if status:
            print("\nMicrophone warning:", status)

        audio_data = bytes(indata)

        def enqueue():
            if not audio_queue.full():
                audio_queue.put_nowait(audio_data)

        loop.call_soon_threadsafe(enqueue)

    print("\nStarting microphone...")

    # State is maintained between chunks so resampling
    # remains continuous.

    resample_state = None

    with sd.RawInputStream(
        device=MIC_DEVICE,
        samplerate=INPUT_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=BLOCK_SIZE,
        callback=microphone_callback
    ):

        print("Microphone ready.")
        print("AIRA is listening...\n")

        while True:

            audio_data = await audio_queue.get()

            # Convert 44.1 kHz audio to 16 kHz.
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


# ==================================================
# RECEIVE TRANSCRIPTIONS
# ==================================================

async def transcription_receiver(session):

    while True:

        async for response in session.receive():

            content = response.server_content

            if content is None:
                continue

            # Only finalized transcripts are displayed.

            transcription = content.input_transcription

            if transcription and transcription.text:

                text = transcription.text.strip()

                if text:

                    timestamp = datetime.now().strftime(
                        "%H:%M:%S"
                    )

                    print("\n" + "-" * 50)

                    print(
                        f"[{timestamp}] YOU: {text}"
                    )

                    print("-" * 50)

                    print("\nAIRA is listening...")


# ==================================================
# MAIN SESSION
# ==================================================

async def main():

    audio_queue = asyncio.Queue(
        maxsize=QUEUE_SIZE
    )

    print("\n====================================")
    print("       AIRA LIVE TRANSCRIPTION")
    print("====================================")

    print("Model:", MODEL)
    print("Microphone:", MIC_DEVICE)
    print("Input:", INPUT_RATE, "Hz")
    print("Output:", OUTPUT_RATE, "Hz")

    print("\nConnecting to Gemini Live...")

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print("\nGemini connected successfully!")

        await asyncio.gather(

            microphone_sender(
                session,
                audio_queue
            ),

            transcription_receiver(
                session
            )

        )


# ==================================================
# START AIRA
# ==================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\n\nAIRA stopped.")

    except Exception as error:

        print("\nAIRA ERROR")
        print("Type:", type(error).__name__)
        print("Details:", error)