"""Tiny fixture package for supervisor tests (golden cases G1-G5)."""


def add(a: float, b: float) -> float:
    return a - b


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean() of empty list")
    return sum(values) / len(values)
