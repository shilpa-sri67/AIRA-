import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from voice.speech_to_text import gemini_stt
from voice.text_to_speech import aira_tts
from voice.audio_manger import audio_manager

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize with Gemini Flash TTS")
    play_local: bool = Field(default=False, description="Whether to play audio on local host speakers")


class MicListenRequest(BaseModel):
    duration: int = Field(default=5, description="Seconds to listen to microphone")


@router.post("/transcribe", tags=["Voice"])
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Gemini 3.5 Transcribe Live endpoint:
    Upload an audio file (wav/mp3/webm), transcribes using Gemini Live STT.
    """
    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            transcribed_text = gemini_stt.transcribe_audio_file(tmp_path)
            return {
                "status": "success",
                "filename": file.filename,
                "transcribed_text": transcribed_text,
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/speak", tags=["Voice"])
def speak_endpoint(request: SpeakRequest):
    """
    Gemini 3.8 Flash TTS endpoint:
    Synthesize text into speech ("AIRA SPEAKS").
    Returns audio file or URL.
    """
    try:
        audio_path = aira_tts.synthesize(request.text)
        if request.play_local:
            aira_tts.play_audio(audio_path, block=False)

        filename = os.path.basename(audio_path)
        media_type = "audio/mpeg" if audio_path.endswith(".mp3") else "audio/wav"

        return FileResponse(
            path=audio_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.post("/mic-listen", tags=["Voice"])
def listen_microphone_endpoint(request: MicListenRequest):
    """
    End-to-End Voice Cycle:
    Records microphone -> Gemini 3.5 Transcribe Live -> Agent Core (Gemini 3.8 Flash)
    -> Tool Router (OS/App/IoT) -> Verification -> Response Generation -> Gemini TTS.
    """
    try:
        result = audio_manager.listen_and_process(duration=request.duration)
        return {
            "status": "success",
            "pipeline": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice pipeline failed: {str(e)}")

