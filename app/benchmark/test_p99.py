from app.latency.metrics import (
    percentile,
)


def main():

    print("=" * 80)
    print("P99 LATENCY TEST")
    print("=" * 80)

    latency_samples = [
        80,
        82,
        85,
        87,
        90,
        92,
        95,
        98,
        100,
        102,
        105,
        108,
        110,
        112,
        115,
        118,
        120,
        125,
        130,
        135,
        140,
        145,
        150,
        155,
        160,
        170,
        180,
        200,
        350,
        900,
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

    p95 = percentile(
        latency_samples,
        95,
    )

    p99 = percentile(
        latency_samples,
        99,
    )

    print("\n" + "-" * 80)

    print(
        f"P50 latency: {p50} ms"
    )

    print(
        f"P95 latency: {p95} ms"
    )

    print(
        f"P99 latency: {p99} ms"
    )

    print("-" * 80)

    print(
        "\nInterpretation:"
    )

    print(
        "P50 represents the typical request."
    )

    print(
        "P95 represents the slower tail."
    )

    print(
        "P99 represents the extreme tail."
    )

    print(
        "\nP99 is useful for identifying "
        "rare but very slow requests."
    )


if __name__ == "__main__":
    main()