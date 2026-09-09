import queue
import threading
import time
from pathlib import Path
from typing import Any

from app.services.groq_streaming import (
    GroqStreamingService,
)
from app.services.groq_tts import (
    GroqTTSService,
)


class RealtimeVoicePipeline:
    """
    Real-time LLM -> Chunker -> TTS pipeline.

    LLM generation and TTS generation operate concurrently.
    """

    def __init__(self):

        self.llm = GroqStreamingService()

        self.tts = GroqTTSService()

        self.chunk_queue = queue.Queue()

        self.audio_results = []

        self.turn_start_time = None

        self.first_token_time = None
        self.first_chunk_time = None
        self.first_tts_start_time = None
        self.first_audio_time = None
        self.llm_end_time = None
        self.pipeline_end_time = None

    # ==========================================================
    # LLM PRODUCER
    # ==========================================================

    def llm_worker(
        self,
        user_message: str,
    ):

        def on_chunk(
            speech_chunk: str,
        ):

            if self.first_chunk_time is None:

                self.first_chunk_time = (
                    time.perf_counter()
                )

            print()
            print(
                "[LLM → QUEUE]"
            )

            print(
                speech_chunk
            )

            self.chunk_queue.put(
                speech_chunk
            )

        result = self.llm.stream_response(
            user_message=user_message,
            on_chunk=on_chunk,
        )

        # ----------------------------------------------
        # Capture TTFT
        # ----------------------------------------------

        if result["ttft_ms"] is not None:

            self.first_token_time = (
                self.turn_start_time
                + (
                    result["ttft_ms"]
                    / 1000
                )
            )

        self.llm_end_time = (
            time.perf_counter()
        )

        # ----------------------------------------------
        # Tell consumer that LLM is finished
        # ----------------------------------------------

        self.chunk_queue.put(
            None
        )

        return result

    # ==========================================================
    # TTS CONSUMER
    # ==========================================================

    def tts_worker(
        self,
        output_directory: str,
    ):

        output_dir = Path(
            output_directory
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        chunk_number = 0

        while True:

            speech_chunk = (
                self.chunk_queue.get()
            )

            # ------------------------------------------
            # Sentinel
            # ------------------------------------------

            if speech_chunk is None:

                break

            chunk_number += 1

            print()
            print(
                f"[QUEUE → TTS] Chunk "
                f"{chunk_number}"
            )

            print(
                speech_chunk
            )

            # ------------------------------------------
            # First TTS start
            # ------------------------------------------

            if self.first_tts_start_time is None:

                self.first_tts_start_time = (
                    time.perf_counter()
                )

            audio_filename = (
                f"realtime_chunk_"
                f"{chunk_number}.wav"
            )

            result = self.tts.synthesize(
                text=speech_chunk,
                output_filename=audio_filename,
            )

            # ------------------------------------------
            # First usable audio
            # ------------------------------------------

            if self.first_audio_time is None:

                self.first_audio_time = (
                    time.perf_counter()
                )

                print()
                print(
                    ">>> FIRST AUDIO AVAILABLE <<<"
                )

            self.audio_results.append(
                {
                    "chunk_index": chunk_number,
                    "text": speech_chunk,
                    "audio_path": result[
                        "audio_path"
                    ],
                    "tts_latency_ms": result[
                        "tts_latency_ms"
                    ],
                }
            )

            print(
                f"Audio generated: "
                f"{result['audio_path']}"
            )

    # ==========================================================
    # RUN PIPELINE
    # ==========================================================

    def run(
        self,
        user_message: str,
        output_directory: str = (
            "data/audio/realtime"
        ),
    ) -> dict[str, Any]:

        self.turn_start_time = (
            time.perf_counter()
        )

        print()
        print("=" * 80)
        print("REAL-TIME VOICE PIPELINE")
        print("=" * 80)

        print()
        print("User:")
        print(user_message)

        # ======================================================
        # Start TTS consumer FIRST
        # ======================================================

        tts_thread = threading.Thread(
            target=self.tts_worker,
            args=(output_directory,),
            daemon=True,
        )

        tts_thread.start()

        # ======================================================
        # Start LLM producer
        # ======================================================

        llm_result_holder = {}

        def run_llm():

            result = self.llm_worker(
                user_message
            )

            llm_result_holder[
                "result"
            ] = result

        llm_thread = threading.Thread(
            target=run_llm,
            daemon=True,
        )

        llm_thread.start()

        # ======================================================
        # Wait for LLM
        # ======================================================

        llm_thread.join()

        # ======================================================
        # Wait for all TTS work
        # ======================================================

        tts_thread.join()

        self.pipeline_end_time = (
            time.perf_counter()
        )

        # ======================================================
        # Calculate metrics
        # ======================================================

        ttft_ms = None

        if self.first_token_time is not None:

            ttft_ms = round(
                (
                    self.first_token_time
                    - self.turn_start_time
                )
                * 1000,
                2,
            )

        first_chunk_ms = None

        if self.first_chunk_time is not None:

            first_chunk_ms = round(
                (
                    self.first_chunk_time
                    - self.turn_start_time
                )
                * 1000,
                2,
            )

        first_tts_latency_ms = None

        if (
            self.first_tts_start_time
            is not None
            and self.first_audio_time
            is not None
        ):

            first_tts_latency_ms = round(
                (
                    self.first_audio_time
                    - self.first_tts_start_time
                )
                * 1000,
                2,
            )

        ttfa_ms = None

        if self.first_audio_time is not None:

            ttfa_ms = round(
                (
                    self.first_audio_time
                    - self.turn_start_time
                )
                * 1000,
                2,
            )

        total_ms = round(
            (
                self.pipeline_end_time
                - self.turn_start_time
            )
            * 1000,
            2,
        )

        llm_generation_ms = None

        if self.llm_end_time is not None:

            llm_generation_ms = round(
                (
                    self.llm_end_time
                    - self.turn_start_time
                )
                * 1000,
                2,
            )

        # ======================================================
        # Results
        # ======================================================

        result = llm_result_holder.get(
            "result",
            {},
        )

        print()
        print("=" * 80)
        print("REAL-TIME LATENCY RESULTS")
        print("=" * 80)

        print(
            f"TTFT                 : "
            f"{ttft_ms} ms"
        )

        print(
            f"First chunk ready    : "
            f"{first_chunk_ms} ms"
        )

        print(
            f"First TTS latency    : "
            f"{first_tts_latency_ms} ms"
        )

        print(
            f"TTFA                 : "
            f"{ttfa_ms} ms"
        )

        print(
            f"LLM generation      : "
            f"{llm_generation_ms} ms"
        )

        print(
            f"Total pipeline       : "
            f"{total_ms} ms"
        )

        print(
            f"Audio chunks         : "
            f"{len(self.audio_results)}"
        )

        print("=" * 80)

        return {
            "status": "success",
            "user_message": user_message,
            "response": result.get(
                "response",
                "",
            ),
            "audio": self.audio_results,
            "latency": {
                "ttft_ms": ttft_ms,
                "first_chunk_ms": first_chunk_ms,
                "first_tts_latency_ms": (
                    first_tts_latency_ms
                ),
                "ttfa_ms": ttfa_ms,
                "llm_generation_ms": (
                    llm_generation_ms
                ),
                "total_ms": total_ms,
            },
        }