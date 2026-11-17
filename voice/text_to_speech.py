import os
import time
import asyncio
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("aira.tts")


class AiraTTS:
    """
    GEMINI 3.8 FLASH TTS / SPEECH SYNTHESIS ENGINE
    Synthesizes conversational responses into speech ("AIRA SPEAKS").
    Supports Gemini Speech Output, Edge-TTS (high quality neural voice), and Pyttsx3 (local).
    Plays audio through speakers or writes audio file for frontend streaming.
    """

    def __init__(self):
        self.engine_type = settings.TTS_ENGINE
        self.voice = settings.TTS_VOICE
        self.api_key = settings.GEMINI_API_KEY
        self.gemini_client = None

        if self.api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini TTS client: {e}")

    async def _synthesize_edge_tts(self, text: str, output_path: str):
        """High-speed neural speech synthesis using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def _synthesize_pyttsx3(self, text: str, output_path: str):
        """Offline speech synthesis using pyttsx3."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)
        # Select female voice if available
        voices = engine.getProperty("voices")
        for v in voices:
            if "zira" in v.name.lower() or "female" in v.name.lower() or "aria" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        engine.save_to_file(text, output_path)
        engine.runAndWait()

    def synthesize(self, text: str, output_filename: Optional[str] = None) -> str:
        """
        Synthesize text to speech and save to an audio file.
        Returns the absolute path to the generated audio file.
        """
        cache_dir = os.path.join(os.getcwd(), "cache", "audio")
        os.makedirs(cache_dir, exist_ok=True)
        fname = output_filename or f"aira_speech_{int(time.time()*1000)}.mp3"
        output_path = os.path.join(cache_dir, fname)

        # 1. Edge-TTS (Natural Neural Voice)
        try:
            asyncio.run(self._synthesize_edge_tts(text, output_path))
            logger.info(f"Synthesized speech via Edge-TTS ({self.voice}) to {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Edge-TTS failed: {e}. Falling back to pyttsx3...")

        # 2. Pyttsx3 Fallback
        try:
            wav_path = output_path.replace(".mp3", ".wav")
            self._synthesize_pyttsx3(text, wav_path)
            logger.info(f"Synthesized speech via Pyttsx3 to {wav_path}")
            return wav_path
        except Exception as e:
            logger.error(f"Pyttsx3 synthesis failed: {e}")
            raise RuntimeError(f"All TTS synthesis engines failed: {e}")

    def speak(self, text: str, block: bool = True) -> str:
        """
        Synthesize and immediately play audio on speakers ("AIRA SPEAKS").
        """
        audio_file = self.synthesize(text)
        self.play_audio(audio_file, block=block)
        return audio_file

    def play_audio(self, audio_file_path: str, block: bool = True):
        """
        Play the synthesized audio file locally on Windows.
        """
        try:
            import winsound
            if audio_file_path.endswith(".wav"):
                flag = winsound.SND_FILENAME
                if not block:
                    flag |= winsound.SND_ASYNC
                winsound.PlaySound(audio_file_path, flag)
                return
        except Exception:
            pass

        # Try PowerShell Media.SoundPlayer or Windows Media Player background spawn
        try:
            ps_script = f"""
            Add-Type -AssemblyName presentationCore
            $player = New-Object System.Windows.Media.MediaPlayer
            $player.Open('{audio_file_path.replace(chr(92), "/")}')
            $player.Play()
            Start-Sleep -Seconds 3
            """
            import subprocess
            subprocess.Popen(["powershell", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Audio playback failed: {e}")


aira_tts = AiraTTS()


def speak(text: str) -> str:
    """Convenience functional wrapper."""
    return aira_tts.speak(text)

