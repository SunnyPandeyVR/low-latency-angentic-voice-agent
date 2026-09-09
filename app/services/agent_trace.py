import time
from typing import Any


class AgentTrace:
    """
    Lightweight in-memory trace for one voice-agent turn.

    Records:
        - Pipeline stages
        - Stage start/end times
        - Stage latency
        - TTFT
        - TTS chunk timings

    This is intentionally simple for the interview POC.
    """

    def __init__(self):

        self.trace_id = (
            f"trace-{int(time.time() * 1000)}"
        )

        self.pipeline_start = (
            time.perf_counter()
        )

        self.events: list[dict[str, Any]] = []

    def record(
        self,
        stage: str,
        event: str,
        **metadata: Any,
    ) -> None:
        """
        Record one trace event.
        """

        elapsed_ms = round(
            (
                time.perf_counter()
                - self.pipeline_start
            )
            * 1000,
            2,
        )

        self.events.append(
            {
                "stage": stage,
                "event": event,
                "elapsed_ms": elapsed_ms,
                **metadata,
            }
        )

    def stage(
        self,
        stage: str,
        start_event: str = "started",
        end_event: str = "completed",
    ):
        """
        Context manager for measuring a stage.

        Usage:

            with trace.stage("stt"):
                ...

        """

        return _TraceStage(
            trace=self,
            stage=stage,
            start_event=start_event,
            end_event=end_event,
        )

    def get_trace(self) -> dict[str, Any]:
        """
        Return the complete trace.
        """

        total_ms = round(
            (
                time.perf_counter()
                - self.pipeline_start
            )
            * 1000,
            2,
        )

        return {
            "trace_id": self.trace_id,
            "total_elapsed_ms": total_ms,
            "events": self.events,
        }


class _TraceStage:
    """
    Internal context manager used by AgentTrace.stage().
    """

    def __init__(
        self,
        trace: AgentTrace,
        stage: str,
        start_event: str,
        end_event: str,
    ):

        self.trace = trace
        self.stage_name = stage
        self.start_event = start_event
        self.end_event = end_event

        self.start_time = None

    def __enter__(self):

        self.start_time = time.perf_counter()

        self.trace.record(
            self.stage_name,
            self.start_event,
        )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        if self.start_time is not None:

            latency_ms = round(
                (
                    time.perf_counter()
                    - self.start_time
                )
                * 1000,
                2,
            )

        else:

            latency_ms = None

        self.trace.record(
            self.stage_name,
            self.end_event,
            latency_ms=latency_ms,
        )

        return False
