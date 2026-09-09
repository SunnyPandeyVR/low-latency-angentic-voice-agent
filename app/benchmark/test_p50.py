from app.latency.metrics import (
    percentile,
)


def main():

    print("=" * 80)
    print("P50 LATENCY TEST")
    print("=" * 80)

    latency_samples = [
        100,
        110,
        120,
        125,
        130,
        135,
        140,
        145,
        150,
        500,
    ]

    print("\nLatency samples:")

    for index, latency in enumerate(
        latency_samples,
        start=1,
    ):

        print(
            f"Request {index:02d}: "
            f"{latency} ms"
        )

    p50 = percentile(
        latency_samples,
        50,
    )

    print("\n" + "-" * 80)

    print(
        f"P50 latency: {p50} ms"
    )

    print("-" * 80)

    print(
        "\nInterpretation:"
    )

    print(
        "50% of requests completed "
        "at or below the P50 latency."
    )

    print(
        "\nThe 500 ms request is an outlier."
    )

    print(
        "P50 is therefore much closer to "
        "the normal user experience than the maximum."
    )


if __name__ == "__main__":
    main()
    