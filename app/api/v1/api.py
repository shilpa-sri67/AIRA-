from fastapi import APIRouter
from app.api.v1.endpoints import health, agent, voice, iot, live_ws

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router, tags=["Health"])

# Python Agent Core (Decision + Planning + Tool Router + Verification)
api_router.include_router(agent.router, prefix="/agent", tags=["Agent Core"])

# Voice (Microphone -> Gemini Live STT & Gemini Flash TTS -> AIRA Speaks)
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])

# Smart Home IoT Control (Lights, Plugs, AC/Thermostat, Scenes)
api_router.include_router(iot.router, prefix="/iot", tags=["IoT Control"])

# Real-time WebSocket Live Stream
api_router.include_router(live_ws.router, tags=["Live Streaming"])
