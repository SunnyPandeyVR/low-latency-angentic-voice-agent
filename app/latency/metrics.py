from typing import Optional


def percentile(
    values: list[float],
    percentile_value: float,
) -> Optional[float]:
    """
    Calculate a percentile using linear interpolation.

    Example:
        percentile(values, 50) -> P50
        percentile(values, 95) -> P95
        percentile(values, 99) -> P99
    """

    if not values:
        return None

    if not 0 <= percentile_value <= 100:
        raise ValueError(
            "percentile_value must be between 0 and 100."
        )

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return round(sorted_values[0], 2)

    position = (
        percentile_value
        / 100
        * (len(sorted_values) - 1)
    )

    lower_index = int(position)
    upper_index = lower_index + 1

    if upper_index >= len(sorted_values):
        return round(
            sorted_values[lower_index],
            2,
        )

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    fraction = position - lower_index

    result = (
        lower_value
        + (upper_value - lower_value)
        * fraction
    )

    return round(result, 2)


def calculate_latency_statistics(
    values: list[float],
) -> dict:

    if not values:
        return {
            "count": 0,
            "average_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "min_ms": None,
            "max_ms": None,
        }

    return {
        "count": len(values),

        "average_ms": round(
            sum(values) / len(values),
            2,
        ),

        "p50_ms": percentile(
            values,
            50,
        ),

        "p95_ms": percentile(
            values,
            95,
        ),

        "p99_ms": percentile(
            values,
            99,
        ),

        "min_ms": round(
            min(values),
            2,
        ),

        "max_ms": round(
            max(values),
            2,
        ),
    }