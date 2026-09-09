from app.latency.baseline_comparison import (
    compare_latency,
    print_comparison,
)


def main():

    print("=" * 90)
    print("BASELINE VS OPTIMIZED TEST")
    print("=" * 90)

    # --------------------------------------------------------------
    # DEMONSTRATION DATA
    #
    # These are example values only.
    # They are NOT real measurements.
    # --------------------------------------------------------------

    baseline = {
        "stt_latency": 420.0,
        "ttft": 350.0,
        "chunk_ready": 430.0,
        "tts_latency": 500.0,
        "ttfa": 930.0,
        "total_turn": 1450.0,
    }

    optimized = {
        "stt_latency": 400.0,
        "ttft": 180.0,
        "chunk_ready": 240.0,
        "tts_latency": 320.0,
        "ttfa": 560.0,
        "total_turn": 900.0,
    }

    comparison = compare_latency(
        baseline,
        optimized,
    )

    print_comparison(
        comparison
    )

    print("\nInterpretation:")
    print(
        "Positive improvement means the "
        "optimized pipeline reduced latency."
    )

    print(
        "\nNOTE:"
    )

    print(
        "The values above are demonstration values."
    )

    print(
        "Real benchmark values will be collected "
        "from the running voice pipeline."
    )


if __name__ == "__main__":
    main()
    