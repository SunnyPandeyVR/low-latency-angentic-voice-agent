import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class VoiceLatencyMeasurement:
    """
    Stores latency timestamps for one voice-agent turn.

    Timeline:

        turn start
            ↓
        first LLM token
            ↓
        first speech chunk
            ↓
        TTS start
            ↓
        first audio available
    """

    turn_start_time: float

    first_token_time: Optional[float] = None
    first_speech_chunk_time: Optional[float] = None
    tts_start_time: Optional[float] = None
    first_audio_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def ttft_ms(self) -> Optional[float]:
        if self.first_token_time is None:
            return None

        return round(
            (self.first_token_time - self.turn_start_time) * 1000,
            2,
        )

    @property
    def chunk_ready_ms(self) -> Optional[float]:
        if self.first_speech_chunk_time is None:
            return None

        return round(
            (
                self.first_speech_chunk_time
                - self.turn_start_time
            )
            * 1000,
            2,
        )

    @property
    def tts_latency_ms(self) -> Optional[float]:
        if (
            self.tts_start_time is None
            or self.first_audio_time is None
        ):
            return None

        return round(
            (
                self.first_audio_time
                - self.tts_start_time
            )
            * 1000,
            2,
        )

    @property
    def ttfa_ms(self) -> Optional[float]:
        """
        Time from beginning of the turn until
        first usable audio is available.
        """

        if self.first_audio_time is None:
            return None

        return round(
            (
                self.first_audio_time
                - self.turn_start_time
            )
            * 1000,
            2,
        )

    @property
    def total_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None

        return round(
            (
                self.end_time
                - self.turn_start_time
            )
            * 1000,
            2,
        )


class VoiceLatencyTimer:
    """
    Timer for measuring end-to-end voice-agent latency.
    """

    def __init__(self):
        self.measurement = VoiceLatencyMeasurement(
            turn_start_time=time.perf_counter()
        )

    def mark_first_token(self):
        if self.measurement.first_token_time is None:
            self.measurement.first_token_time = (
                time.perf_counter()
            )

    def mark_first_speech_chunk(self):
        if self.measurement.first_speech_chunk_time is None:
            self.measurement.first_speech_chunk_time = (
                time.perf_counter()
            )

    def mark_tts_start(self):
        if self.measurement.tts_start_time is None:
            self.measurement.tts_start_time = (
                time.perf_counter()
            )

    def mark_first_audio(self):
        if self.measurement.first_audio_time is None:
            self.measurement.first_audio_time = (
                time.perf_counter()
            )

    def stop(self):
        self.measurement.end_time = time.perf_counter()

    @property
    def ttft_ms(self):
        return self.measurement.ttft_ms

    @property
    def chunk_ready_ms(self):
        return self.measurement.chunk_ready_ms

    @property
    def tts_latency_ms(self):
        return self.measurement.tts_latency_ms

    @property
    def ttfa_ms(self):
        return self.measurement.ttfa_ms

    @property
    def total_ms(self):
        return self.measurement.total_ms