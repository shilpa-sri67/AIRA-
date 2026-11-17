import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agent_core import agent_core
from voice.speech_to_text import gemini_stt
from voice.text_to_speech import aira_tts

router = APIRouter()
logger = logging.getLogger("aira.websocket")


@router.websocket("/ws/live")
async def websocket_live_pipeline(websocket: WebSocket):
    """
    Real-time WebSocket Live Stream Endpoint:
    Connects AIRA Frontend directly to the Live Pipeline.
    Supports streaming audio or text messages, emitting events for:
    - Transcribed text
    - Decision & Planning
    - Tool execution & Verification
    - Response Generation
    - Gemini Flash TTS audio
    """
    await websocket.accept()
    await websocket.send_json({
        "event": "connected",
        "message": "AIRA Live Pipeline WebSocket connected.",
    })

    try:
        while True:
            # Check message format: can be JSON text or binary audio chunk
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]
                # 1. Gemini Live STT
                await websocket.send_json({"event": "status", "stage": "transcribing"})
                transcribed = gemini_stt.transcribe_bytes(audio_bytes)
                await websocket.send_json({"event": "transcribed", "text": transcribed})

                if not transcribed:
                    continue
                user_text = transcribed

            elif "text" in message and message["text"]:
                payload = json.loads(message["text"])
                msg_type = payload.get("type", "text")

                if msg_type == "ping":
                    await websocket.send_json({"event": "pong"})
                    continue

                user_text = payload.get("message", "")
            else:
                continue

            # 2. Decision & Planning via Python Agent Core
            await websocket.send_json({
                "event": "planning",
                "message": f"Processing query: '{user_text}' with Gemini 3.8 Flash..."
            })

            # Process with Agent Core
            result = agent_core.process(user_text)

            # 3. Tool Execution & Verification Events
            for tool_call in result.get("tools_called", []):
                await websocket.send_json({
                    "event": "tool_executed",
                    "domain": tool_call.get("domain"),
                    "tool": tool_call.get("tool"),
                    "verified": tool_call.get("verified"),
                    "status": tool_call.get("status"),
                    "result": tool_call.get("result"),
                    "verification_notes": tool_call.get("verification_notes"),
                })

            reply_text = result["text"]

            # 4. Response Generation & 5. TTS ("AIRA SPEAKS")
            audio_url = None
            try:
                speech_file = aira_tts.synthesize(reply_text)
                audio_filename = speech_file.replace("\\", "/").split("/")[-1]
                audio_url = f"/audio/{audio_filename}"
            except Exception as e:
                logger.warning(f"TTS synthesis failed during websocket session: {e}")

            await websocket.send_json({
                "event": "response",
                "reply": reply_text,
                "audio_url": audio_url,
                "tools_called": result.get("tools_called", []),
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass

