import os
import time
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("aira.stt")

# Attempt loading faster-whisper for offline/instant fallback
whisper_model = None
def get_whisper():
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Initializing local WhisperModel fallback...")
            whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        except Exception as e:
            logger.warning(f"Could not initialize local faster-whisper: {e}")
    return whisper_model


class GeminiLiveSTT:
    """
    GEMINI 3.5 TRANSCRIBE LIVE / STT MODULE
    Transcribes live audio or recorded audio chunks using Gemini Live transcription,
    with automatic offline fallback to faster-whisper.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_LIVE_STT_MODEL
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini Live STT configured with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini STT client: {e}")

    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using Gemini Live Transcribe / Gemini Audio model.
        Falls back to local Whisper if API is unavailable.
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        start_time = time.time()
        logger.info(f"Transcribing audio from {audio_file_path}...")

        # 1. Try Gemini Audio Transcription
        if self.client:
            try:
                from google.genai import types
                with open(audio_file_path, "rb") as f:
                    audio_bytes = f.read()

                # Determine mime type
                mime = "audio/wav" if audio_file_path.lower().endswith(".wav") else "audio/mp3"

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                        "Transcribe the spoken words in this audio exactly. Return only the transcribed text with no extra commentary or formatting.",
                    ],
                )
                text = (response.text or "").strip()
                latency = round(time.time() - start_time, 2)
                logger.info(f"Gemini Live Transcribed: '{text}' (latency: {latency}s)")
                if text:
                    return text
            except Exception as e:
                logger.warning(f"Gemini transcription failed, trying local fallback: {e}")

        # 2. Local Fallback (faster-whisper)
        whisper = get_whisper()
        if whisper:
            try:
                segments, info = whisper.transcribe(audio_file_path, beam_size=5)
                text = " ".join(seg.text.strip() for seg in segments).strip()
                latency = round(time.time() - start_time, 2)
                logger.info(f"Local Whisper Transcribed: '{text}' (latency: {latency}s, language: {info.language})")
                return text
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}")

        return "Speech could not be transcribed."

    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav") -> str:
        """
        Transcribe raw audio bytes (useful for WebSocket live streaming).
        """
        cache_dir = os.path.join(os.getcwd(), "cache", "audio")
        os.makedirs(cache_dir, exist_ok=True)
        temp_file = os.path.join(cache_dir, f"temp_stream_{int(time.time()*1000)}.{format}")

        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        try:
            return self.transcribe_audio_file(temp_file)
        finally:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass


gemini_stt = GeminiLiveSTT()


def transcribe_audio(audio_file: str) -> str:
    """Convenience functional wrapper."""
    return gemini_stt.transcribe_audio_file(audio_file)
