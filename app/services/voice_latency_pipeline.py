import time
from pathlib import Path
from typing import Any

from app.latency.voice_metrics import VoiceLatencyTimer
from app.services.groq_streaming import GroqStreamingService
from app.services.groq_tts import GroqTTSService
from app.services.response_chunker import ResponseChunker


class VoiceLatencyPipeline:
    """
    End-to-end latency pipeline.

    Measures:

        TTFT
        Chunk Ready
        TTS latency
        TTFA
        Total latency
    """

    def __init__(self):
        self.llm = GroqStreamingService()
        self.tts = GroqTTSService()

    def run(
        self,
        user_message: str,
        output_directory: str = "data/audio/ttfa",
    ) -> dict[str, Any]:

        timer = VoiceLatencyTimer()

        chunker = ResponseChunker(
            min_chunk_length=20,
            max_chunk_length=180,
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print()
        print("=" * 80)
        print("VOICE LATENCY PIPELINE")
        print("=" * 80)

        print()
        print("User:")
        print(user_message)

        print()
        print("Starting LLM streaming...")

        start_time = time.perf_counter()

        # ---------------------------------------------------------
        # Start LLM stream
        # ---------------------------------------------------------

        stream_result = self.llm.stream_response(
            user_message
        )

        # ---------------------------------------------------------
        # NOTE
        # ---------------------------------------------------------
        #
        # The current GroqStreamingService implementation
        # consumes the complete stream internally.
        #
        # Therefore this POC cannot observe each token directly
        # from here.
        #
        # We still use the recorded TTFT from the streaming
        # service and then process the resulting speech chunks.
        #
        # A fully overlapped producer/consumer pipeline will be
        # implemented when we move beyond the basic POC.
        # ---------------------------------------------------------

        llm_ttft = stream_result.get(
            "ttft_ms"
        )

        if llm_ttft is not None:
            print(
                f"LLM TTFT: {llm_ttft:.2f} ms"
            )

        speech_chunks = stream_result.get(
            "speech_chunks",
            []
        )

        full_response = stream_result.get(
            "response",
            ""
        )

        print()
        print(
            f"Speech chunks generated: "
            f"{len(speech_chunks)}"
        )

        # ---------------------------------------------------------
        # Mark first chunk
        # ---------------------------------------------------------

        if speech_chunks:
            timer.measurement.first_token_time = (
                timer.measurement.turn_start_time
                + (
                    llm_ttft / 1000
                    if llm_ttft is not None
                    else 0
                )
            )

            timer.mark_first_speech_chunk()

        generated_audio = []

        # ---------------------------------------------------------
        # TTS each speech chunk
        # ---------------------------------------------------------

        for index, chunk in enumerate(
            speech_chunks,
            start=1,
        ):

            print()
            print(
                f"[Chunk {index}]"
            )

            print(
                f"Text: {chunk}"
            )

            # First TTS request starts here
            if index == 1:
                timer.mark_tts_start()

            tts_start = time.perf_counter()

            audio_filename = (
                f"chunk_{index}.wav"
            )

            result = self.tts.synthesize(
                text=chunk,
                output_filename=audio_filename,
            )

            tts_end = time.perf_counter()

            print(
                f"TTS latency: "
                f"{result['tts_latency_ms']:.2f} ms"
            )

            print(
                f"Audio: "
                f"{result['audio_path']}"
            )

            # First usable audio is available
            if index == 1:
                timer.mark_first_audio()

            generated_audio.append(
                {
                    "chunk_index": index,
                    "text": chunk,
                    "audio_path": result[
                        "audio_path"
                    ],
                    "tts_latency_ms": result[
                        "tts_latency_ms"
                    ],
                }
            )

        # ---------------------------------------------------------
        # Stop timer
        # ---------------------------------------------------------

        timer.stop()

        # ---------------------------------------------------------
        # Metrics
        # ---------------------------------------------------------

        print()
        print("=" * 80)
        print("LATENCY RESULTS")
        print("=" * 80)

        print(
            f"TTFT              : "
            f"{timer.ttft_ms} ms"
        )

        print(
            f"First chunk ready  : "
            f"{timer.chunk_ready_ms} ms"
        )

        print(
            f"First TTS latency  : "
            f"{timer.tts_latency_ms} ms"
        )

        print(
            f"TTFA               : "
            f"{timer.ttfa_ms} ms"
        )

        print(
            f"Total pipeline     : "
            f"{timer.total_ms} ms"
        )

        print("=" * 80)

        return {
            "status": "success",
            "user_message": user_message,
            "response": full_response,
            "speech_chunks": speech_chunks,
            "audio": generated_audio,
            "latency": {
                "ttft_ms": timer.ttft_ms,
                "first_chunk_ready_ms": (
                    timer.chunk_ready_ms
                ),
                "first_tts_latency_ms": (
                    timer.tts_latency_ms
                ),
                "ttfa_ms": timer.ttfa_ms,
                "total_ms": timer.total_ms,
            },
        }