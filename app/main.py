import os
import tempfile
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    UploadFile,
)
from fastapi.responses import (
    FileResponse,
)

from app.agents.router import AgentRouter
from app.config import GROQ_API_KEY
from app.services.groq_agent import GroqAgent
from app.services.groq_stt import GroqSTTService
from app.services.groq_streaming import (
    GroqStreamingService,
)

from app.api.voice_websocket import (
    router as voice_websocket_router,
)


BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="Low Latency Agentic Voice",
    description=(
        "Voice AI POC for latency "
        "and agentic AI engineering"
    ),
    version="0.4.0",
)


stt_service = GroqSTTService()

agent = GroqAgent()

streaming_service = (
    GroqStreamingService()
)

router = AgentRouter()


app.include_router(
    voice_websocket_router
)


@app.get("/")
def root():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "groq_configured": bool(
            GROQ_API_KEY
        ),
        "stt_model": stt_service.model,
        "llm_model": agent.model,
    }


@app.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...)
):

    suffix = os.path.splitext(
        audio.filename or ".wav"
    )[1]

    audio_bytes = await audio.read()

    if not audio_bytes:

        return {
            "status": "error",
            "message": "Audio file is empty.",
        }

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(
                audio_bytes
            )

            temp_path = temp_file.name


        result = (
            stt_service.transcribe(
                temp_path
            )
        )


        return {
            "status": "success",
            "filename": audio.filename,
            "transcript": result["text"],
            "stt_latency_ms": (
                result["latency_ms"]
            ),
            "model": result["model"],
        }


    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(
                temp_path
            )


@app.post("/agent/stream")
async def stream_agent(
    message: str
):

    result = (
        streaming_service
        .stream_response(
            message
        )
    )

    return {
        "status": "success",
        "user_message": message,
        **result,
    }


@app.post("/agent")
async def run_agent(
    message: str
):

    result = agent.run(
        message
    )

    return {
        "status": "success",
        "user_message": message,
        **result,
    }