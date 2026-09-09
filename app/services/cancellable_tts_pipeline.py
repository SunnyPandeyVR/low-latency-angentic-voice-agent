import queue
from threading import Event, Thread
from typing import Optional

from app.services.groq_tts import GroqTTSService


class CancellableTTSPipeline:
    """
    Producer-consumer TTS pipeline.

    Text chunks are placed into a queue.

    A worker consumes chunks and sends them to TTS.

    When cancel_event is set:
        - pending chunks are discarded
        - new TTS requests are not started
    """

    def __init__(self):

        self.tts_service = (
            GroqTTSService()
        )

        self.queue = queue.Queue()

        self.cancel_event = Event()

        self.worker: Optional[Thread] = None

        self.chunk_number = 0

    def start(self):

        self.cancel_event.clear()

        self.worker = Thread(
            target=self._worker,
            daemon=True,
        )

        self.worker.start()

    def add_chunk(
        self,
        text: str,
    ):

        if not text.strip():
            return

        if self.cancel_event.is_set():

            print(
                "[TTS] Ignoring chunk because "
                "TTS is cancelled."
            )

            return

        self.queue.put(text)

    def cancel(self):

        print(
            "[TTS] Cancellation requested."
        )

        self.cancel_event.set()

        self._clear_pending_chunks()

    def wait(self):

        if self.worker is not None:

            self.worker.join(
                timeout=5.0
            )

    def _clear_pending_chunks(self):

        cleared = 0

        while True:

            try:

                self.queue.get_nowait()

                self.queue.task_done()

                cleared += 1

            except queue.Empty:

                break

        if cleared:

            print(
                f"[TTS] Discarded "
                f"{cleared} pending chunks."
            )

    def _worker(self):

        print(
            "[TTS] Worker started."
        )

        while True:

            try:

                text = self.queue.get(
                    timeout=0.2
                )

            except queue.Empty:

                if (
                    self.cancel_event.is_set()
                    and self.queue.empty()
                ):
                    break

                continue

            try:

                if self.cancel_event.is_set():

                    print(
                        "[TTS] Skipping cancelled chunk."
                    )

                    continue

                self.chunk_number += 1

                filename = (
                    f"realtime_chunk_"
                    f"{self.chunk_number}.wav"
                )

                result = (
                    self.tts_service.synthesize(
                        text=text,
                        output_filename=filename,
                        cancel_event=(
                            self.cancel_event
                        ),
                    )
                )

                if (
                    result["status"]
                    == "cancelled"
                ):

                    print(
                        "[TTS] Chunk cancelled."
                    )

                else:

                    print(
                        "[TTS] Chunk generated:",
                        result["audio_path"],
                    )

            finally:

                self.queue.task_done()

        print(
            "[TTS] Worker stopped."
        )