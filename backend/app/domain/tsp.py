from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

from app.domain.cost_model import RoutingOptions
from app.domain.protocols import DistanceProvider


@dataclass(frozen=True)
class Stop:
    order_id: str
    kind: str  # "pickup" or "dropoff"
    node_id: str


@dataclass(frozen=True)
class Tour:
    ordered_stops: list[Stop]
    total_distance_meters: float
    optimal: bool


def _check_precedence(stops: list[Stop]) -> bool:
    """Check that for each order, pickup appears before dropoff."""
    seen: dict[str, str] = {}  # order_id -> first kind seen
    for stop in stops:
        if stop.order_id not in seen:
            seen[stop.order_id] = stop.kind
        elif stop.kind == "pickup" and seen[stop.order_id] == "dropoff":
            return False
    return True


def _tour_distance(stops: list[Stop], cost_matrix: DistanceProvider) -> float:
    """Compute total distance for a sequence of stops."""
    if len(stops) < 2:
        return 0.0

    total = 0.0
    for i in range(len(stops) - 1):
        dist = cost_matrix.get_distance(stops[i].node_id, stops[i + 1].node_id)
        if dist is None or dist == float("inf"):
            return float("inf")
        total += dist
    return total


def _brute_force_optimal(
    stops: list[Stop],
    cost_matrix: DistanceProvider,
) -> tuple[list[Stop], float] | None:
    """Find optimal tour by trying all valid permutations.

    Only feasible for small n (≤ 10 stops).
    Returns (best_stops, best_distance) or None if no valid tour.
    """
    best_stops = None
    best_dist = float("inf")

    for perm in permutations(stops):
        if not _check_precedence(list(perm)):
            continue
        dist = _tour_distance(list(perm), cost_matrix)
        if dist < best_dist:
            best_dist = dist
            best_stops = list(perm)

    if best_stops is None:
        return None
    return best_stops, best_dist


def _is_dropoff_eligible(
    stop: Stop,
    visited_orders: dict[str, set[str]],
    remaining: list[Stop],
) -> bool:
    """Check if a dropoff stop can be visited (pickup already done or no pickup left)."""
    if stop.kind != "dropoff":
        return True
    visited = visited_orders.get(stop.order_id, set())
    if "pickup" in visited:
        return True
    has_pickup_remaining = any(
        s.order_id == stop.order_id and s.kind == "pickup" for s in remaining
    )
    return not has_pickup_remaining


def _find_nearest_valid_stop(
    remaining: list[Stop],
    current_node: str,
    visited_orders: dict[str, set[str]],
    cost_matrix: DistanceProvider,
) -> int:
    """Find the index of the nearest valid stop; -1 if none."""
    best_idx = -1
    best_dist = float("inf")

    for i, stop in enumerate(remaining):
        if not _is_dropoff_eligible(stop, visited_orders, remaining):
            continue
        dist = cost_matrix.get_distance(current_node, stop.node_id)
        if dist is not None and dist < best_dist:
            best_dist = dist
            best_idx = i

    return best_idx


def _nearest_neighbor_heuristic(
    stops: list[Stop],
    cost_matrix: DistanceProvider,
    start_node: str | None = None,
) -> list[Stop] | None:
    """Nearest-neighbor heuristic respecting precedence constraints.

    Starts from start_node (or first stop's node if not given).
    At each step, pick the nearest unvisited stop that doesn't violate precedence.
    """
    if not stops:
        return []

    remaining = list(stops)
    result: list[Stop] = []
    visited_orders: dict[str, set[str]] = {}

    current_node = _initialize_start(
        remaining, result, visited_orders, start_node
    )

    while remaining:
        best_idx = _find_nearest_valid_stop(
            remaining, current_node, visited_orders, cost_matrix
        )
        if best_idx < 0:
            return None

        chosen = remaining.pop(best_idx)
        result.append(chosen)
        visited_orders.setdefault(chosen.order_id, set()).add(chosen.kind)
        current_node = chosen.node_id

    return result


def _initialize_start(
    remaining: list[Stop],
    result: list[Stop],
    visited_orders: dict[str, set[str]],
    start_node: str | None,
) -> str:
    """Set up the starting point for nearest-neighbor; return current node."""
    if start_node:
        return start_node
    first = remaining.pop(0)
    result.append(first)
    visited_orders.setdefault(first.order_id, set()).add(first.kind)
    return first.node_id


def _two_opt_improve(
    stops: list[Stop],
    cost_matrix: DistanceProvider,
    max_iterations: int = 100,
) -> list[Stop]:
    """2-opt local search improvement respecting precedence."""
    if len(stops) < 4:
        return stops

    current = list(stops)
    current_dist = _tour_distance(current, cost_matrix)

    for _ in range(max_iterations):
        result = _find_2opt_move(current, current_dist, cost_matrix)
        if result is None:
            break
        current, current_dist = result

    return current


def _find_2opt_move(
    current: list[Stop],
    current_dist: float,
    cost_matrix: DistanceProvider,
) -> tuple[list[Stop], float] | None:
    """Find a single improving 2-opt move; return (new_stops, new_dist) or None."""
    for i in range(len(current) - 1):
        for j in range(i + 2, len(current)):
            candidate = current[:i + 1] + current[i + 1:j + 1][::-1] + current[j + 1:]
            if not _check_precedence(candidate):
                continue
            candidate_dist = _tour_distance(candidate, cost_matrix)
            if candidate_dist < current_dist:
                return candidate, candidate_dist
    return None


def optimize_tour(
    shipper_node: str,
    stops: list[Stop],
    cost_matrix: DistanceProvider,
    *,
    n_small_threshold: int | None = None,
    options: RoutingOptions | None = None,
) -> Tour:
    """Optimize a tour for a single shipper visiting multiple stops.

    Constraints:
    - Pickup of each order must come before its dropoff
    - Start from shipper_node

    For n ≤ threshold: brute-force optimal.
    For n > threshold: nearest-neighbor + 2-opt heuristic.

    Threshold resolution order:
    1. `options.tsp_brute_force_max_stops` (if `options` given)
    2. `n_small_threshold` (explicit override)
    3. `RoutingOptions.DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS` (8)

    A threshold of 0 disables the brute-force path entirely.
    """
    if not stops:
        return Tour(ordered_stops=[], total_distance_meters=0.0, optimal=True)

    # Resolve threshold: options > explicit kwarg > default
    if options is not None:
        threshold = options.resolved_tsp_threshold()
    elif n_small_threshold is not None:
        threshold = n_small_threshold
    else:
        from app.domain.cost_model import DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS
        threshold = DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS

    # Add shipper start as first stop conceptually
    # For brute-force, we need to consider all permutations of stops
    # starting from shipper_node

    n = len(stops)

    if threshold > 0 and n <= threshold:
        # Try brute-force with shipper_node as fixed start
        result = _brute_force_with_start(stops, shipper_node, cost_matrix)
        if result:
            best_stops, best_dist = result
            return Tour(
                ordered_stops=best_stops,
                total_distance_meters=best_dist,
                optimal=True,
            )

    # Heuristic: nearest-neighbor + 2-opt
    nn_result = _nearest_neighbor_heuristic(stops, cost_matrix, shipper_node)
    if nn_result is None:
        # No valid tour found
        return Tour(
            ordered_stops=[],
            total_distance_meters=float("inf"),
            optimal=False,
        )

    improved = _two_opt_improve(nn_result, cost_matrix)

    # Compute total distance including start
    total = 0.0
    current = shipper_node
    for stop in improved:
        dist = cost_matrix.get_distance(current, stop.node_id)
        if dist is None:
            dist = float("inf")
        total += dist
        current = stop.node_id

    return Tour(
        ordered_stops=improved,
        total_distance_meters=total,
        optimal=False,
    )


def _brute_force_with_start(
    stops: list[Stop],
    start_node: str,
    cost_matrix: DistanceProvider,
) -> tuple[list[Stop], float] | None:
    """Brute-force with fixed start node."""
    best_stops = None
    best_dist = float("inf")

    for perm in permutations(stops):
        if not _check_precedence(list(perm)):
            continue

        # Compute distance: start -> perm[0] -> perm[1] -> ...
        total = 0.0
        current = start_node
        valid = True
        for stop in perm:
            dist = cost_matrix.get_distance(current, stop.node_id)
            if dist is None or dist == float("inf"):
                valid = False
                break
            total += dist
            current = stop.node_id

        if valid and total < best_dist:
            best_dist = total
            best_stops = list(perm)

    if best_stops is None:
        return None
    return best_stops, best_dist
