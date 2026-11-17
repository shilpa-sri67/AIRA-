import os
import time
import logging
from typing import Optional, Dict, Any
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

from app.core.config import settings
from voice.speech_to_text import gemini_stt
from voice.text_to_speech import aira_tts
from backend.agent_core import agent_core

logger = logging.getLogger("aira.voice_manager")


class AudioManager:
    """
    VOICE PIPELINE MANAGER
    Orchestrates:
    AIRA FRONTEND / MICROPHONE
       -> Gemini 3.5 Transcribe Live
       -> Transcribed Text
       -> Python Agent Core (Gemini 3.8 Flash)
       -> Decision + Planning & Tool Router (OS / App / IoT)
       -> Verification
       -> Response Generation
       -> Gemini 3.8 Flash TTS
       -> AIRA SPEAKS
    """

    def __init__(self, sample_rate: int = 16000, duration: int = 5):
        self.sample_rate = sample_rate
        self.duration = duration
        self.cache_dir = os.path.join(os.getcwd(), "cache", "audio")
        os.makedirs(self.cache_dir, exist_ok=True)

    def record_microphone(self, duration: Optional[int] = None) -> str:
        """
        Record audio from microphone for specified seconds and save as WAV.
        """
        dur = duration or self.duration
        output_file = os.path.join(self.cache_dir, f"mic_input_{int(time.time()*1000)}.wav")

        print(f"\n[AIRA Voice] Listening for {dur} seconds... Speak now!")
        audio = sd.rec(
            int(dur * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        write(output_file, self.sample_rate, audio)
        print("[AIRA Voice] Recording finished. Processing speech...")
        return output_file

    def listen_and_process(self, duration: Optional[int] = None) -> dict:
        """
        Full end-to-end cycle:
        1. Capture Microphone
        2. Transcribe Live (Gemini 3.5 Transcribe Live)
        3. Agent Core (Gemini 3.8 Flash)
        4. Tool Router (OS / App / IoT)
        5. Verification
        6. Response Generation
        7. Speak Response (Gemini Flash TTS)
        """
        # Step 1: Microphone
        audio_file = self.record_microphone(duration=duration)

        # Step 2: Gemini 3.5 Transcribe Live
        print("\n[Pipeline Step 1] Transcribing audio with Gemini Live...")
        transcribed_text = gemini_stt.transcribe_audio_file(audio_file)
        print(f"-> Transcribed Text: \"{transcribed_text}\"")

        if not transcribed_text or transcribed_text.strip() == "":
            return {
                "transcribed_text": "",
                "response": "I didn't catch that. Could you please repeat?",
                "tools": [],
            }

        # Step 3: Python Agent Core (Gemini 3.8 Flash Decision + Planning + Tools + Verification)
        print("\n[Pipeline Step 2] Python Agent Core (Gemini 3.8 Flash) Reasoning & Planning...")
        agent_result = agent_core.process(transcribed_text)
        reply_text = agent_result["text"]
        tools_called = agent_result.get("tools_called", [])

        if tools_called:
            print(f"[Pipeline Step 3] Tool Router & Verification:")
            for t in tools_called:
                print(f"  * Tool: {t.get('tool')} [{t.get('domain')}] | Verified: {t.get('verified')} | Status: {t.get('status')}")

        print(f"\n[Pipeline Step 4] Response Generation: \"{reply_text}\"")

        # Step 5: Gemini 3.8 Flash TTS ("AIRA SPEAKS")
        print("\n[Pipeline Step 5] Synthesizing Voice (AIRA SPEAKS)...")
        speech_file = aira_tts.speak(reply_text, block=False)

        return {
            "transcribed_text": transcribed_text,
            "response": reply_text,
            "tools_called": tools_called,
            "speech_file": speech_file,
        }


audio_manager = AudioManager()
