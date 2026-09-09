import asyncio
import statistics
import time

import httpx


BASE_URL = "http://127.0.0.1:8000"

ENDPOINT = "/agent/stream"

MESSAGE = (
    "Explain what a low latency voice agent is "
    "in two short sentences."
)


CONCURRENCY_LEVELS = [
    1,
    2,
    5,
    10,
]


async def send_request(
    client: httpx.AsyncClient,
    request_id: int,
) -> dict:

    start_time = time.perf_counter()

    try:

        response = await client.post(
            f"{BASE_URL}{ENDPOINT}",
            params={
                "message": MESSAGE
            },
            timeout=120.0,
        )

        end_time = time.perf_counter()

        latency_ms = (
            end_time - start_time
        ) * 1000

        return {
            "request_id": request_id,
            "status_code": response.status_code,
            "latency_ms": round(
                latency_ms,
                2,
            ),
            "success": (
                response.status_code == 200
            ),
        }

    except Exception as exc:

        end_time = time.perf_counter()

        latency_ms = (
            end_time - start_time
        ) * 1000

        return {
            "request_id": request_id,
            "status_code": None,
            "latency_ms": round(
                latency_ms,
                2,
            ),
            "success": False,
            "error": str(exc),
        }


async def run_concurrency_test(
    concurrency: int,
) -> list[dict]:

    print(
        f"\nRunning "
        f"{concurrency} concurrent requests..."
    )

    async with httpx.AsyncClient() as client:

        tasks = [
            send_request(
                client,
                request_id,
            )
            for request_id in range(
                1,
                concurrency + 1,
            )
        ]

        results = await asyncio.gather(
            *tasks
        )

    return results


def calculate_statistics(
    results: list[dict],
) -> dict:

    latencies = [
        result["latency_ms"]
        for result in results
        if result["success"]
    ]

    if not latencies:

        return {
            "successful": 0,
            "failed": len(results),
            "average_ms": None,
            "min_ms": None,
            "max_ms": None,
        }

    return {
        "successful": len(latencies),
        "failed": (
            len(results)
            - len(latencies)
        ),
        "average_ms": round(
            statistics.mean(latencies),
            2,
        ),
        "min_ms": round(
            min(latencies),
            2,
        ),
        "max_ms": round(
            max(latencies),
            2,
        ),
    }


async def main():

    print("=" * 90)
    print("CONCURRENCY BENCHMARK")
    print("=" * 90)

    print(
        f"\nEndpoint: "
        f"{BASE_URL}{ENDPOINT}"
    )

    print(
        f"Message: {MESSAGE}"
    )

    all_results = []

    for concurrency in CONCURRENCY_LEVELS:

        results = await run_concurrency_test(
            concurrency
        )

        stats = calculate_statistics(
            results
        )

        all_results.append(
            {
                "concurrency": concurrency,
                **stats,
            }
        )

        print(
            f"\nConcurrency: {concurrency}"
        )

        print(
            f"Successful : "
            f"{stats['successful']}"
        )

        print(
            f"Failed     : "
            f"{stats['failed']}"
        )

        print(
            f"Average    : "
            f"{stats['average_ms']} ms"
        )

        print(
            f"Min        : "
            f"{stats['min_ms']} ms"
        )

        print(
            f"Max        : "
            f"{stats['max_ms']} ms"
        )

    print("\n" + "=" * 90)
    print("CONCURRENCY SUMMARY")
    print("=" * 90)

    print(
        f"{'Concurrency':<15}"
        f"{'Successful':<15}"
        f"{'Failed':<12}"
        f"{'Average':<15}"
        f"{'Min':<15}"
        f"{'Max':<15}"
    )

    print("-" * 90)

    for result in all_results:

        print(
            f"{result['concurrency']:<15}"
            f"{result['successful']:<15}"
            f"{result['failed']:<12}"
            f"{str(result['average_ms']) + ' ms':<15}"
            f"{str(result['min_ms']) + ' ms':<15}"
            f"{str(result['max_ms']) + ' ms':<15}"
        )

    print("=" * 90)

    print(
        "\nConcurrency benchmark complete."
    )


if __name__ == "__main__":

    asyncio.run(main())