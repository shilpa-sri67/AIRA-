from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agent_core import agent_core
from backend.tools.router import tool_router
from voice.text_to_speech import aira_tts

router = APIRouter()


class InteractRequest(BaseModel):
    message: str = Field(..., description="User query or transcribed speech")
    generate_speech: bool = Field(default=True, description="Whether to synthesize speech for the response")


class ToolExecutionRecord(BaseModel):
    verified: bool
    tool: Optional[str] = None
    domain: Optional[str] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    verification_notes: Optional[str] = None


class InteractResponse(BaseModel):
    status: str
    input_text: str
    reply_text: str
    tools_called: List[Dict[str, Any]]
    audio_url: Optional[str] = None
    engine: Optional[str] = None


@router.post("/interact", response_model=InteractResponse, tags=["Agent Core"])
def interact_with_aira(request: InteractRequest) -> InteractResponse:
    """
    Main Agent Core Interaction Endpoint:
    1. Receives input text (from user or live transcription)
    2. Runs Python Agent Core (Gemini 3.8 Flash)
    3. Executes Decision + Planning -> Tool Router (OS Control, App Control, IoT Control)
    4. Runs Verification on tool executions
    5. Produces final verified Response Generation
    6. Optionally synthesizes speech (Gemini Flash TTS)
    """
    try:
        agent_result = agent_core.process(request.message)
        reply_text = agent_result["text"]
        tools_called = agent_result.get("tools_called", [])
        engine = agent_result.get("engine", "gemini")

        audio_url = None
        if request.generate_speech and reply_text:
            try:
                speech_file = aira_tts.synthesize(reply_text)
                audio_filename = speech_file.replace("\\", "/").split("/")[-1]
                audio_url = f"/audio/{audio_filename}"
            except Exception:
                pass

        return InteractResponse(
            status="success",
            input_text=request.message,
            reply_text=reply_text,
            tools_called=tools_called,
            audio_url=audio_url,
            engine=engine,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@router.get("/tools", tags=["Agent Core"])
def list_tools():
    """
    List all tools available in the Tool Router (OS Control, App Control, IoT Control).
    """
    return {
        "status": "success",
        "count": len(tool_router.get_tool_declarations()),
        "tools": tool_router.get_tool_declarations(),
    }

