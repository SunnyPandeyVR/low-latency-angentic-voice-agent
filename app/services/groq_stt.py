import os
import time
from pathlib import Path

from groq import Groq


class GroqSTTService:
    """
    Speech-to-text service using Groq Whisper.

    This class deliberately measures the latency of the
    STT operation so that it can later become part of our
    complete voice latency pipeline.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(api_key=api_key)

        self.model = "whisper-large-v3-turbo"

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe an audio file and return the transcript
        together with latency information.
        """

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        start_time = time.perf_counter()

        with open(path, "rb") as audio_file:

            transcription = self.client.audio.transcriptions.create(
                file=audio_file,
                model=self.model,
                response_format="json",
            )

        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000

        transcript = transcription.text

        return {
            "text": transcript,
            "latency_ms": round(latency_ms, 2),
            "model": self.model,
        }