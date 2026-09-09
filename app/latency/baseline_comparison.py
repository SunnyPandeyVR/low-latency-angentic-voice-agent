from typing import Any


def calculate_improvement(
    baseline_ms: float,
    optimized_ms: float,
) -> float:
    """
    Calculate percentage latency reduction.

    Positive value:
        Optimized system is faster.

    Negative value:
        Optimized system is slower.
    """

    if baseline_ms <= 0:
        raise ValueError(
            "Baseline latency must be greater than zero."
        )

    improvement = (
        (baseline_ms - optimized_ms)
        / baseline_ms
    ) * 100

    return round(
        improvement,
        2,
    )


def compare_latency(
    baseline: dict[str, float],
    optimized: dict[str, float],
) -> dict[str, Any]:
    """
    Compare baseline and optimized latency
    for each pipeline metric.
    """

    metrics = set(baseline.keys()) & set(
        optimized.keys()
    )

    comparison = {}

    for metric in metrics:

        baseline_value = baseline[metric]
        optimized_value = optimized[metric]

        improvement = calculate_improvement(
            baseline_value,
            optimized_value,
        )

        comparison[metric] = {
            "baseline_ms": baseline_value,
            "optimized_ms": optimized_value,
            "improvement_percent": improvement,
        }

    return comparison


def print_comparison(
    comparison: dict[str, Any],
):
    """
    Print a readable baseline-vs-optimized table.
    """

    print("\n" + "=" * 90)
    print("BASELINE VS OPTIMIZED LATENCY")
    print("=" * 90)

    print(
        f"{'Metric':<25}"
        f"{'Baseline':>15}"
        f"{'Optimized':>15}"
        f"{'Improvement':>18}"
    )

    print("-" * 90)

    for metric, values in comparison.items():

        baseline = values["baseline_ms"]
        optimized = values["optimized_ms"]
        improvement = values[
            "improvement_percent"
        ]

        print(
            f"{metric:<25}"
            f"{baseline:>12.2f} ms"
            f"{optimized:>12.2f} ms"
            f"{improvement:>15.2f}%"
        )

    print("=" * 90)