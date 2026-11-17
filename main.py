import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import health_check

# Ensure cache directory exists for audio streaming
audio_dir = os.path.join(os.getcwd(), "cache", "audio")
os.makedirs(audio_dir, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AIRA Personal AI Assistant - Modular FastAPI Backend with Gemini Live Voice & Tool Control",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration to allow React frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static audio files directory for frontend playback
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Direct /health endpoint
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])

# Versioned API routes under /api/v1 (e.g. /api/v1/health, /api/v1/agent, /api/v1/voice, /api/v1/iot)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION,
        "architecture": {
            "stt": "Gemini 3.5 Transcribe Live",
            "agent_core": "Gemini 3.8 Flash (Decision + Planning)",
            "router": "Tool Router (OS, App, IoT Control) + Verification",
            "tts": "Gemini 3.8 Flash TTS",
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
