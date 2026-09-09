from app.latency.metrics import (
    percentile,
)


def main():

    print("=" * 80)
    print("P95 LATENCY TEST")
    print("=" * 80)

    latency_samples = [
        100,
        105,
        110,
        115,
        120,
        125,
        130,
        135,
        140,
        145,
        150,
        155,
        160,
        165,
        170,
        175,
        180,
        185,
        190,
        200,
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

    p95 = percentile(
        latency_samples,
        95,
    )

    print("\n" + "-" * 80)

    print(
        f"P95 latency: {p95} ms"
    )

    print("-" * 80)

    print(
        "\nInterpretation:"
    )

    print(
        "95% of requests completed "
        "at or below the P95 latency."
    )

    print(
        "\nOnly the slowest 5% of requests "
        "are above P95."
    )


if __name__ == "__main__":
    main()