import time


from app.services.cancellable_tts_pipeline import (
    CancellableTTSPipeline,
)


def test_tts_cancellation():

    print("=" * 80)
    print("TTS CANCELLATION TEST")
    print("=" * 80)

    pipeline = (
        CancellableTTSPipeline()
    )

    pipeline.start()

    # -------------------------------------------------------------
    # Add several speech chunks.
    # -------------------------------------------------------------

    pipeline.add_chunk(
        "This is the first response chunk."
    )

    pipeline.add_chunk(
        "This is the second response chunk."
    )

    pipeline.add_chunk(
        "This is the third response chunk."
    )

    pipeline.add_chunk(
        "This is the fourth response chunk."
    )

    print(
        "\n[TTS TEST] Chunks queued."
    )

    # Give the worker a short opportunity
    # to start processing.

    time.sleep(0.2)

    # -------------------------------------------------------------
    # SIMULATE BARGE-IN
    # -------------------------------------------------------------

    print(
        "\n[BARGE-IN] User started speaking."
    )

    pipeline.cancel()

    # -------------------------------------------------------------
    # WAIT FOR WORKER
    # -------------------------------------------------------------

    pipeline.wait()

    print(
        "\n[TTS TEST] Pipeline stopped."
    )

    print("=" * 80)
    print("TTS CANCELLATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":

    test_tts_cancellation()