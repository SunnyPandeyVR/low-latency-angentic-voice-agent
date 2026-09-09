import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PerHopMetrics:
    """
    Stores latency measurements for every major
    stage of a low-latency voice interaction.

    All timestamps use time.perf_counter()
    so measurements are suitable for latency benchmarking.
    """

    turn_start_time: float

    stt_start_time: Optional[float] = None
    stt_end_time: Optional[float] = None

    llm_start_time: Optional[float] = None
    first_token_time: Optional[float] = None
    llm_end_time: Optional[float] = None

    chunk_ready_time: Optional[float] = None

    tts_start_time: Optional[float] = None
    first_audio_time: Optional[float] = None
    tts_end_time: Optional[float] = None

    turn_end_time: Optional[float] = None

    # ------------------------------------------------------------------
    # MARK TIMESTAMPS
    # ------------------------------------------------------------------

    def mark_stt_start(self):
        self.stt_start_time = time.perf_counter()

    def mark_stt_end(self):
        self.stt_end_time = time.perf_counter()

    def mark_llm_start(self):
        self.llm_start_time = time.perf_counter()

    def mark_first_token(self):
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()

    def mark_llm_end(self):
        self.llm_end_time = time.perf_counter()

    def mark_chunk_ready(self):
        if self.chunk_ready_time is None:
            self.chunk_ready_time = time.perf_counter()

    def mark_tts_start(self):
        if self.tts_start_time is None:
            self.tts_start_time = time.perf_counter()

    def mark_first_audio(self):
        if self.first_audio_time is None:
            self.first_audio_time = time.perf_counter()

    def mark_tts_end(self):
        self.tts_end_time = time.perf_counter()

    def mark_turn_end(self):
        self.turn_end_time = time.perf_counter()

    # ------------------------------------------------------------------
    # LATENCY CALCULATIONS
    # ------------------------------------------------------------------

    @staticmethod
    def _milliseconds(
        start: Optional[float],
        end: Optional[float],
    ) -> Optional[float]:

        if start is None or end is None:
            return None

        return round(
            (end - start) * 1000,
            2,
        )

    @property
    def stt_latency_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.stt_start_time,
            self.stt_end_time,
        )

    @property
    def ttft_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.llm_start_time,
            self.first_token_time,
        )

    @property
    def llm_generation_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.llm_start_time,
            self.llm_end_time,
        )

    @property
    def chunk_ready_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.llm_start_time,
            self.chunk_ready_time,
        )

    @property
    def tts_latency_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.tts_start_time,
            self.tts_end_time,
        )

    @property
    def ttfa_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.turn_start_time,
            self.first_audio_time,
        )

    @property
    def llm_to_audio_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.llm_start_time,
            self.first_audio_time,
        )

    @property
    def total_turn_ms(self) -> Optional[float]:

        return self._milliseconds(
            self.turn_start_time,
            self.turn_end_time,
        )

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:

        return {
            "stt_latency_ms": self.stt_latency_ms,

            "ttft_ms": self.ttft_ms,

            "chunk_ready_ms": self.chunk_ready_ms,

            "tts_latency_ms": self.tts_latency_ms,

            "ttfa_ms": self.ttfa_ms,

            "llm_generation_ms": (
                self.llm_generation_ms
            ),

            "llm_to_audio_ms": (
                self.llm_to_audio_ms
            ),

            "total_turn_ms": (
                self.total_turn_ms
            ),
        }