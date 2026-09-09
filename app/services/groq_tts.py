import os
import time
from pathlib import Path
from threading import Event
from typing import Any, Optional

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class GroqTTSService:
    """
    Groq Text-to-Speech service.

    Supports:
        - Text-to-speech generation
        - WAV output
        - TTS latency measurement
        - Cancellation before a TTS request starts

    Note:
        Groq's current TTS request is handled as a generated audio
        response. The cancellation implemented here prevents queued
        TTS work from starting after a barge-in.
    """

    def __init__(self):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = os.getenv(
            "GROQ_TTS_MODEL",
            "canopylabs/orpheus-v1-english",
        )

        self.voice = os.getenv(
            "GROQ_TTS_VOICE",
            "autumn",
        )

        self.output_directory = Path(
            os.getenv(
                "TTS_OUTPUT_DIR",
                "data/audio",
            )
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def synthesize(
        self,
        text: str,
        output_filename: str = "tts_output.wav",
        cancel_event: Optional[Event] = None,
    ) -> dict[str, Any]:

        if not text.strip():

            raise ValueError(
                "TTS text cannot be empty."
            )

        # =========================================================
        # CHECK CANCELLATION BEFORE TTS
        # =========================================================

        if (
            cancel_event is not None
            and cancel_event.is_set()
        ):

            print(
                "[TTS] Cancelled before synthesis."
            )

            return {
                "status": "cancelled",
                "text": text,
                "model": self.model,
                "voice": self.voice,
                "audio_path": None,
                "tts_latency_ms": None,
            }

        start_time = time.perf_counter()

        output_path = (
            self.output_directory
            / output_filename
        )

        print(
            f"[TTS] Synthesizing: {text[:80]}"
        )

        response = (
            self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                response_format="wav",
                input=text,
            )
        )

        # =========================================================
        # CHECK AGAIN AFTER API RESPONSE
        # =========================================================

        if (
            cancel_event is not None
            and cancel_event.is_set()
        ):

            print(
                "[TTS] Cancelled after synthesis "
                "response arrived."
            )

            return {
                "status": "cancelled",
                "text": text,
                "model": self.model,
                "voice": self.voice,
                "audio_path": None,
                "tts_latency_ms": round(
                    (
                        time.perf_counter()
                        - start_time
                    )
                    * 1000,
                    2,
                ),
            }

        response.write_to_file(
            str(output_path)
        )

        end_time = time.perf_counter()

        tts_latency_ms = round(
            (
                end_time
                - start_time
            )
            * 1000,
            2,
        )

        file_size_bytes = (
            output_path.stat().st_size
        )

        return {
            "status": "success",
            "text": text,
            "model": self.model,
            "voice": self.voice,
            "audio_format": "wav",
            "audio_path": str(output_path),
            "audio_size_bytes": file_size_bytes,
            "tts_latency_ms": tts_latency_ms,
        }