from __future__ import annotations

from dataclasses import dataclass


# Default solver thresholds. Exposed on RoutingOptions so callers can tune the
# brute-force cutoff for the TSP (`optimize_tour`) and VRP (`solve_vrp`)
# solvers. The defaults are conservative: brute-force is O(n!) and only safe
# for very small instances.
DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS = 8
DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS = 3
DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS = 2


@dataclass(frozen=True)
class RoutingOptions:
    avoid_road_types: tuple[str, ...] = ()
    avoid_edge_ids: tuple[str, ...] = ()
    # Solver thresholds. `None` means "use the module-level default". Setting
    # to 0 disables the brute-force path entirely (always heuristic).
    tsp_brute_force_max_stops: int | None = None
    vrp_brute_force_max_orders: int | None = None
    vrp_brute_force_max_shippers: int | None = None

    def resolved_tsp_threshold(self) -> int:
        return (
            DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS
            if self.tsp_brute_force_max_stops is None
            else self.tsp_brute_force_max_stops
        )

    def resolved_vrp_order_threshold(self) -> int:
        return (
            DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS
            if self.vrp_brute_force_max_orders is None
            else self.vrp_brute_force_max_orders
        )

    def resolved_vrp_shipper_threshold(self) -> int:
        return (
            DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS
            if self.vrp_brute_force_max_shippers is None
            else self.vrp_brute_force_max_shippers
        )


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

