from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingOptions:
    avoid_road_types: tuple[str, ...] = ()
    avoid_edge_ids: tuple[str, ...] = ()


DEFAULT_ROAD_MULTIPLIERS: dict[str, float] = {
    "default": 1.0,
    "highway": 0.8,
    "residential": 1.2,
    "tertiary": 1.1,
    "secondary": 1.0,
    "primary": 0.9,
    "trunk": 0.85,
}


def edge_cost(distance: float, road_type: str, options: RoutingOptions) -> float:
    """Compute effective edge cost = distance × multiplier(road_type).

    Returns float('inf') if the road_type is in avoid_road_types.
    """
    if road_type in options.avoid_road_types:
        return float("inf")
    multiplier = DEFAULT_ROAD_MULTIPLIERS.get(road_type, 1.0)
    return distance * multiplier
