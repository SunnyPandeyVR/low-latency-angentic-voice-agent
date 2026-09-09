import os
import time
from threading import Event
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from groq import Groq

from app.services.response_chunker import ResponseChunker


load_dotenv()


class GroqStreamingService:
    """
    Groq streaming LLM service.

    Supports:
        - Token streaming
        - TTFT measurement
        - Response chunking
        - Real-time chunk callbacks
        - LLM interruption
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
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

    def stream_response(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        on_chunk: Optional[
            Callable[[str], None]
        ] = None,
        interrupt_event: Optional[Event] = None,
    ) -> dict[str, Any]:

        if not user_message.strip():

            raise ValueError(
                "User message cannot be empty."
            )

        messages = []

        if system_message:

            messages.append(
                {
                    "role": "system",
                    "content": system_message,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        timer_start = time.perf_counter()

        first_token_time = None
        first_chunk_time = None

        response_parts = []
        speech_chunks = []

        interrupted = False

        chunker = ResponseChunker(
            min_chunk_length=20,
            max_chunk_length=180,
        )

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            stream=True,
        )

        for chunk in stream:

            # =====================================================
            # CHECK INTERRUPT SIGNAL
            # =====================================================

            if (
                interrupt_event is not None
                and interrupt_event.is_set()
            ):

                interrupted = True

                print(
                    "[LLM] Interrupt signal detected."
                )

                break

            delta = chunk.choices[0].delta

            content = getattr(
                delta,
                "content",
                None,
            )

            if not content:
                continue

            if first_token_time is None:

                first_token_time = (
                    time.perf_counter()
                )

            response_parts.append(
                content
            )

            ready_chunks = (
                chunker.add_text(content)
            )

            for speech_chunk in ready_chunks:

                if first_chunk_time is None:

                    first_chunk_time = (
                        time.perf_counter()
                    )

                speech_chunks.append(
                    speech_chunk
                )

                if on_chunk:

                    on_chunk(
                        speech_chunk
                    )

        # =========================================================
        # ONLY FLUSH REMAINING TEXT IF NOT INTERRUPTED
        # =========================================================

        if not interrupted:

            remaining = chunker.flush()

            if remaining:

                if first_chunk_time is None:

                    first_chunk_time = (
                        time.perf_counter()
                    )

                speech_chunks.append(
                    remaining
                )

                if on_chunk:

                    on_chunk(
                        remaining
                    )

        end_time = time.perf_counter()

        # =========================================================
        # LATENCY
        # =========================================================

        ttft_ms = None

        if first_token_time is not None:

            ttft_ms = round(
                (
                    first_token_time
                    - timer_start
                )
                * 1000,
                2,
            )

        first_chunk_ms = None

        if first_chunk_time is not None:

            first_chunk_ms = round(
                (
                    first_chunk_time
                    - timer_start
                )
                * 1000,
                2,
            )

        total_ms = round(
            (
                end_time
                - timer_start
            )
            * 1000,
            2,
        )

        response_text = "".join(
            response_parts
        )

        return {
            "status": "interrupted"
            if interrupted
            else "success",
            "model": self.model,
            "response": response_text,
            "speech_chunks": speech_chunks,
            "ttft_ms": ttft_ms,
            "first_chunk_ms": first_chunk_ms,
            "total_ms": total_ms,
            "interrupted": interrupted,
        }