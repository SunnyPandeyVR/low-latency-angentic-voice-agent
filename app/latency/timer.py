import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class LatencyMeasurement:
    """
    Stores timing information for one operation.
    """

    start_time: float
    first_token_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def ttft_ms(self) -> Optional[float]:
        """
        Time from operation start until first token.
        """

        if self.first_token_time is None:
            return None

        return round(
            (self.first_token_time - self.start_time)
            * 1000,
            2,
        )

    @property
    def total_ms(self) -> Optional[float]:
        """
        Total operation duration.
        """

        if self.end_time is None:
            return None

        return round(
            (self.end_time - self.start_time)
            * 1000,
            2,
        )


class LatencyTimer:
    """
    High-resolution timer for LLM latency measurement.
    """

    def __init__(self):
        self.measurement = LatencyMeasurement(
            start_time=time.perf_counter()
        )

    def mark_first_token(self):
        """
        Record the exact moment the first
        meaningful LLM token arrives.
        """

        if (
            self.measurement.first_token_time
            is None
        ):
            self.measurement.first_token_time = (
                time.perf_counter()
            )

    def stop(self):
        """
        Record the end of the operation.
        """

        self.measurement.end_time = (
            time.perf_counter()
        )

    @property
    def ttft_ms(self) -> Optional[float]:
        return self.measurement.ttft_ms

    @property
    def total_ms(self) -> Optional[float]:
        return self.measurement.total_ms