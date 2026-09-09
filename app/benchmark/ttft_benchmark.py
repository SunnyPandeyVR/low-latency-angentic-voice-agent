import os
import statistics

from app.services.groq_streaming import (
    GroqStreamingService,
)
from app.latency.metrics import (
    calculate_latency_statistics,
)


def main():

    number_of_requests = int(
        os.getenv(
            "BENCHMARK_REQUESTS",
            "20",
        )
    )

    service = GroqStreamingService()

    test_message = (
        "Explain what machine learning is "
        "in two short sentences."
    )

    ttft_values = []

    print("=" * 70)
    print("GROQ TTFT BENCHMARK")
    print("=" * 70)

    print(
        f"Requests: {number_of_requests}"
    )

    print()

    for index in range(
        number_of_requests
    ):

        try:

            result = (
                service.stream_response(
                    test_message
                )
            )

            ttft = result["ttft_ms"]

            if ttft is not None:

                ttft_values.append(
                    ttft
                )

                print(
                    f"Request {index + 1:02d}: "
                    f"TTFT = {ttft:.2f} ms"
                )

        except Exception as exc:

            print(
                f"Request {index + 1:02d}: "
                f"ERROR - {exc}"
            )

    print()

    statistics_result = (
        calculate_latency_statistics(
            ttft_values
        )
    )

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"Requests measured : "
        f"{statistics_result['count']}"
    )

    print(
        f"Average TTFT      : "
        f"{statistics_result['average_ms']} ms"
    )

    print(
        f"P50 TTFT          : "
        f"{statistics_result['p50_ms']} ms"
    )

    print(
        f"P95 TTFT          : "
        f"{statistics_result['p95_ms']} ms"
    )

    print(
        f"P99 TTFT          : "
        f"{statistics_result['p99_ms']} ms"
    )

    print(
        f"Minimum           : "
        f"{statistics_result['min_ms']} ms"
    )

    print(
        f"Maximum           : "
        f"{statistics_result['max_ms']} ms"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()