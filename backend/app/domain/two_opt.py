from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def reverse_segment(stops: list[T], i: int, j: int) -> list[T]:
    """Reverse the segment from index i+1 to j inclusive."""
    return stops[: i + 1] + stops[i + 1 : j + 1][::-1] + stops[j + 1 :]


def find_improving_2opt_move(
    current: list[T],
    current_dist: float,
    tour_distance: Callable[[list[T]], float],
    precedence_ok: Callable[[list[T]], bool],
) -> tuple[list[T], float] | None:
    """Find a single improving 2-opt move; return (new_stops, new_dist) or None."""
    for i in range(len(current) - 1):
        for j in range(i + 2, len(current)):
            candidate = reverse_segment(current, i, j)
            if not precedence_ok(candidate):
                continue
            candidate_dist = tour_distance(candidate)
            if candidate_dist < current_dist:
                return candidate, candidate_dist
    return None


def two_opt_improve(
    stops: list[T],
    tour_distance: Callable[[list[T]], float],
    precedence_ok: Callable[[list[T]], bool],
    *,
    max_iterations: int | None = 100,
) -> list[T]:
    """2-opt local search; max_iterations=None runs until no improvement."""
    if len(stops) < 4:
        return stops

    current = list(stops)
    current_dist = tour_distance(current)
    iteration = 0

    while max_iterations is None or iteration < max_iterations:
        result = find_improving_2opt_move(
            current, current_dist, tour_distance, precedence_ok
        )
        if result is None:
            break
        current, current_dist = result
        iteration += 1

    return current