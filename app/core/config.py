import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "AIRA AI Assistant"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"

    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

    # Models Architecture
    # Core reasoning, decision & tool planning
    GEMINI_CORE_MODEL: str = os.getenv("GEMINI_CORE_MODEL", "gemini-3.8-flash")
    # Live transcription model
    GEMINI_LIVE_STT_MODEL: str = os.getenv("GEMINI_LIVE_STT_MODEL", "gemini-3.8-flash")
    # TTS model / voice
    GEMINI_TTS_MODEL: str = os.getenv("GEMINI_TTS_MODEL", "gemini-3.8-flash")
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge_tts")  # "gemini", "edge_tts", "pyttsx3"
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")

    # Audio Recording defaults
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1

    # Offline / local fallback
    OLLAMA_FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen3.5:4b")

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
