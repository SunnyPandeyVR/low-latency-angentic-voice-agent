import time

from app.latency.per_hop_metrics import (
    PerHopMetrics,
)


def main():

    print("=" * 80)
    print("PER-HOP LATENCY METRICS TEST")
    print("=" * 80)

    metrics = PerHopMetrics(
        turn_start_time=time.perf_counter()
    )

    # --------------------------------------------------------------
    # Simulate STT
    # --------------------------------------------------------------

    metrics.mark_stt_start()

    time.sleep(0.05)

    metrics.mark_stt_end()

    # --------------------------------------------------------------
    # Simulate LLM
    # --------------------------------------------------------------

    metrics.mark_llm_start()

    time.sleep(0.03)

    metrics.mark_first_token()

    time.sleep(0.05)

    metrics.mark_chunk_ready()

    time.sleep(0.10)

    metrics.mark_llm_end()

    # --------------------------------------------------------------
    # Simulate TTS
    # --------------------------------------------------------------

    metrics.mark_tts_start()

    time.sleep(0.08)

    metrics.mark_first_audio()

    time.sleep(0.05)

    metrics.mark_tts_end()

    # --------------------------------------------------------------
    # End turn
    # --------------------------------------------------------------

    metrics.mark_turn_end()

    # --------------------------------------------------------------
    # Print metrics
    # --------------------------------------------------------------

    print("\nLatency Metrics")
    print("-" * 80)

    result = metrics.to_dict()

    for name, value in result.items():

        print(
            f"{name:<25} : {value} ms"
        )

    print("-" * 80)

    print("\nPer-hop metrics test complete.")


if __name__ == "__main__":
    main()