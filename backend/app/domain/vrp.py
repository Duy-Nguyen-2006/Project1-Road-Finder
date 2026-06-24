from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product

from app.domain.cost_model import RoutingOptions
from app.domain.protocols import DistanceProvider
from app.domain.tsp import Stop, Tour, _check_precedence, optimize_tour


@dataclass(frozen=True)
class FleetPlan:
    tours: list[tuple[str, Tour]]  # (shipper_id, tour)
    unassigned_order_ids: list[str]
    total_distance_meters: float
    optimal: bool


def _insert_pickup_dropoff(
    stops: list[Stop],
    pickup_pos: int,
    dropoff_pos: int,
    pickup_stop: Stop,
    dropoff_stop: Stop,
) -> list[Stop]:
    candidate = list(stops)
    candidate.insert(pickup_pos, pickup_stop)
    candidate.insert(dropoff_pos + 1, dropoff_stop)
    return candidate


def _compute_tour_distance(
    shipper_node: str,
    stops: list[Stop],
    cost_matrix: DistanceProvider,
) -> float:
    if not stops:
        return 0.0
    total = 0.0
    current = shipper_node
    for stop in stops:
        dist = cost_matrix.get_distance(current, stop.node_id)
        if dist is None:
            return float("inf")
        total += dist
        current = stop.node_id
    return total


def _find_best_insertion(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    tours: dict[str, list[Stop]],
    pickup_stop: Stop,
    dropoff_stop: Stop,
    cost_matrix: DistanceProvider,
) -> tuple[str | None, tuple[int, int] | None, float]:
    """Find the shipper and insertion positions minimizing cost increase."""
    best_shipper: str | None = None
    best_position: tuple[int, int] | None = None
    best_cost_increase = float("inf")

    for sid in shipper_ids:
        snode = shipper_nodes[sid]
        current_stops = tours[sid]
        old_cost = _compute_tour_distance(snode, current_stops, cost_matrix)

        for pickup_pos in range(len(current_stops) + 1):
            cost_increase, position = _best_dropoff_for_pickup(
                current_stops,
                pickup_pos,
                pickup_stop,
                dropoff_stop,
                snode,
                old_cost,
                cost_matrix,
            )
            if cost_increase < best_cost_increase:
                best_cost_increase = cost_increase
                best_shipper = sid
                best_position = position

    return best_shipper, best_position, best_cost_increase


def _best_dropoff_for_pickup(
    current_stops: list[Stop],
    pickup_pos: int,
    pickup_stop: Stop,
    dropoff_stop: Stop,
    snode: str,
    old_cost: float,
    cost_matrix: DistanceProvider,
) -> tuple[float, tuple[int, int] | None]:
    """Find the cheapest dropoff position for a given pickup position."""
    best_increase = float("inf")
    best_position: tuple[int, int] | None = None

    for dropoff_pos in range(pickup_pos, len(current_stops) + 1):
        candidate = _insert_pickup_dropoff(
            current_stops,
            pickup_pos,
            dropoff_pos,
            pickup_stop,
            dropoff_stop,
        )
        if not _check_precedence(candidate):
            continue

        new_cost = _compute_tour_distance(snode, candidate, cost_matrix)
        increase = new_cost - old_cost

        if increase < best_increase:
            best_increase = increase
            best_position = (pickup_pos, dropoff_pos)

    return best_increase, best_position


def _cheapest_insertion(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    orders: list[tuple[str, str, str]],  # (order_id, pickup_node, dropoff_node)
    cost_matrix: DistanceProvider,
) -> dict[str, list[Stop]]:
    """Assign orders to shippers using cheapest insertion heuristic.

    For each order, try inserting (pickup, dropoff) into each shipper's tour
    at the position that increases total distance the least.
    """
    tours: dict[str, list[Stop]] = {sid: [] for sid in shipper_ids}

    for order_id, pickup_node, dropoff_node in orders:
        pickup_stop = Stop(order_id=order_id, kind="pickup", node_id=pickup_node)
        dropoff_stop = Stop(order_id=order_id, kind="dropoff", node_id=dropoff_node)

        best_shipper, best_position, _ = _find_best_insertion(
            shipper_ids,
            shipper_nodes,
            tours,
            pickup_stop,
            dropoff_stop,
            cost_matrix,
        )

        if best_shipper is not None and best_position is not None:
            p_pos, d_pos = best_position
            tours[best_shipper] = _insert_pickup_dropoff(
                tours[best_shipper],
                p_pos,
                d_pos,
                pickup_stop,
                dropoff_stop,
            )

    return tours


def _intra_route_2opt(
    stops: list[Stop],
    cost_matrix: DistanceProvider,
    shipper_node: str,
) -> list[Stop]:
    """2-opt improvement within a single route."""
    if len(stops) < 4:
        return stops

    current = list(stops)
    current_dist = _compute_tour_distance(shipper_node, current, cost_matrix)

    while True:
        improved = _try_2opt_improvement(current, current_dist, cost_matrix, shipper_node)
        if improved is None:
            return current
        current, current_dist = improved


def _try_2opt_improvement(
    current: list[Stop],
    current_dist: float,
    cost_matrix: DistanceProvider,
    shipper_node: str,
) -> tuple[list[Stop], float] | None:
    """Try a single 2-opt move; return improved (stops, dist) or None."""
    for i in range(len(current) - 1):
        for j in range(i + 2, len(current)):
            candidate = _reverse_segment(current, i, j)
            if not _check_precedence(candidate):
                continue

            new_dist = _compute_tour_distance(shipper_node, candidate, cost_matrix)
            if new_dist < current_dist:
                return candidate, new_dist
    return None


def _reverse_segment(stops: list[Stop], i: int, j: int) -> list[Stop]:
    """Reverse the segment from index i+1 to j inclusive."""
    return stops[:i + 1] + stops[i + 1:j + 1][::-1] + stops[j + 1:]


def _try_relocate_order(
    src_sid: str,
    dst_sid: str,
    order_id: str,
    src_stops: list[Stop],
    pickup_idx: int,
    dropoff_idx: int,
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> tuple[list[Stop], list[Stop], float] | None:
    """Try relocating an order from src to dst; return improved result or None."""
    new_src = [s for s in src_stops if s.order_id != order_id]
    pickup_stop = src_stops[pickup_idx]
    dropoff_stop = src_stops[dropoff_idx]

    dst_stops_placeholder: list[Stop] = []
    best_insert = _find_cheapest_insertion_in_tour(
        dst_stops_placeholder,
        pickup_stop,
        dropoff_stop,
        shipper_nodes[dst_sid],
        cost_matrix,
    )
    if best_insert is None:
        return None

    src_cost = _compute_tour_distance(shipper_nodes[src_sid], src_stops, cost_matrix)
    dst_cost = _compute_tour_distance(
        shipper_nodes[dst_sid], dst_stops_placeholder, cost_matrix
    )
    new_src_cost = _compute_tour_distance(shipper_nodes[src_sid], new_src, cost_matrix)
    old_total = src_cost + dst_cost
    new_total = new_src_cost + _compute_tour_distance(
        shipper_nodes[dst_sid], best_insert, cost_matrix
    )

    if new_total < old_total:
        return new_src, best_insert, new_total
    return None


def _find_cheapest_insertion_in_tour(
    dst_stops: list[Stop],
    pickup_stop: Stop,
    dropoff_stop: Stop,
    shipper_node: str,
    cost_matrix: DistanceProvider,
) -> list[Stop] | None:
    """Find the cheapest valid insertion of pickup+dropoff into a tour."""
    best_insert: list[Stop] | None = None
    best_cost = float("inf")

    for p_pos in range(len(dst_stops) + 1):
        for d_pos in range(p_pos, len(dst_stops) + 1):
            candidate = _insert_pickup_dropoff(
                dst_stops,
                p_pos,
                d_pos,
                pickup_stop,
                dropoff_stop,
            )
            if not _check_precedence(candidate):
                continue

            new_dst_cost = _compute_tour_distance(shipper_node, candidate, cost_matrix)
            if new_dst_cost < best_cost:
                best_cost = new_dst_cost
                best_insert = candidate

    return best_insert


def _inter_route_relocate(
    tours: dict[str, list[Stop]],
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> dict[str, list[Stop]]:
    """Try relocating an order from one shipper to another."""
    current = dict(tours)

    while True:
        relocation = _find_inter_route_relocation(current, shipper_nodes, cost_matrix)
        if relocation is None:
            return current
        src_sid, dst_sid, new_src, new_dst = relocation
        current[src_sid] = new_src
        current[dst_sid] = new_dst


def _find_inter_route_relocation(
    current: dict[str, list[Stop]],
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> tuple[str, str, list[Stop], list[Stop]] | None:
    """Find the first improving inter-route relocation, if any."""
    all_sids = list(current.keys())
    for src_sid in all_sids:
        src_stops = current[src_sid]
        if len(src_stops) < 2:
            continue
        relocation = _find_source_relocation(
            src_sid, all_sids, src_stops, shipper_nodes, cost_matrix
        )
        if relocation is not None:
            dst_sid, new_src, new_dst = relocation
            return src_sid, dst_sid, new_src, new_dst
    return None


def _find_source_relocation(
    src_sid: str,
    all_sids: list[str],
    src_stops: list[Stop],
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> tuple[str, list[Stop], list[Stop]] | None:
    """Find the first improving relocation from one source shipper."""
    for order_id, indices in _collect_order_indices(src_stops).items():
        if len(indices) != 2:
            continue
        pickup_idx, dropoff_idx = min(indices), max(indices)
        relocated = _attempt_relocate_to_any_dest(
            src_sid,
            all_sids,
            order_id,
            src_stops,
            pickup_idx,
            dropoff_idx,
            shipper_nodes,
            cost_matrix,
        )
        if relocated is not None:
            new_src, new_dst, dst_sid = relocated
            return dst_sid, new_src, new_dst
    return None


def _collect_order_indices(stops: list[Stop]) -> dict[str, list[int]]:
    """Map order_id to the list of stop indices in a tour."""
    orders_in_tour: dict[str, list[int]] = {}
    for idx, stop in enumerate(stops):
        orders_in_tour.setdefault(stop.order_id, []).append(idx)
    return orders_in_tour


def _attempt_relocate_to_any_dest(
    src_sid: str,
    all_sids: list[str],
    order_id: str,
    src_stops: list[Stop],
    pickup_idx: int,
    dropoff_idx: int,
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> tuple[list[Stop], list[Stop], str] | None:
    """Try relocating an order to every destination shipper; return first improvement."""
    for dst_sid in all_sids:
        if dst_sid == src_sid:
            continue
        result = _try_relocate_order(
            src_sid,
            dst_sid,
            order_id,
            src_stops,
            pickup_idx,
            dropoff_idx,
            shipper_nodes,
            cost_matrix,
        )
        if result is not None:
            new_src, best_insert, _ = result
            return new_src, best_insert, dst_sid
    return None


def _resolve_thresholds(
    options: RoutingOptions | None,
    brute_force_threshold: int | None,
    max_brute_force_shippers: int | None,
) -> tuple[int, int]:
    """Resolve order and shipper thresholds: options > explicit kwargs > defaults."""
    if options is not None:
        return options.resolved_vrp_order_threshold(), options.resolved_vrp_shipper_threshold()

    if brute_force_threshold is None:
        from app.domain.cost_model import DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS
        order_threshold = DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS
    else:
        order_threshold = brute_force_threshold

    if max_brute_force_shippers is None:
        from app.domain.cost_model import DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS
        shipper_threshold = DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS
    else:
        shipper_threshold = max_brute_force_shippers

    return order_threshold, shipper_threshold


def _build_heuristic_fleet(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    orders: list[tuple[str, str, str]],
    cost_matrix: DistanceProvider,
) -> FleetPlan:
    """Build a FleetPlan via cheapest insertion + local search."""
    tours_dict = _cheapest_insertion(shipper_ids, shipper_nodes, orders, cost_matrix)

    for sid in shipper_ids:
        tours_dict[sid] = _intra_route_2opt(
            tours_dict[sid], cost_matrix, shipper_nodes[sid]
        )

    tours_dict = _inter_route_relocate(tours_dict, shipper_nodes, cost_matrix)

    fleet_tours = []
    total_distance = 0.0
    assigned_orders: set[str] = set()
    unassigned_from_inf: set[str] = set()

    for sid in shipper_ids:
        stops = tours_dict[sid]
        dist = _compute_tour_distance(shipper_nodes[sid], stops, cost_matrix)
        if dist == float("inf"):
            unassigned_from_inf.update(stop.order_id for stop in stops)
            fleet_tours.append((sid, Tour(
                ordered_stops=[],
                total_distance_meters=0.0,
                optimal=False,
            )))
            continue
        fleet_tours.append((sid, Tour(
            ordered_stops=stops,
            total_distance_meters=dist,
            optimal=False,
        )))
        total_distance += dist
        assigned_orders.update(stop.order_id for stop in stops)

    unassigned = [
        oid
        for oid, _, _ in orders
        if oid not in assigned_orders or oid in unassigned_from_inf
    ]
    unassigned = list(dict.fromkeys(unassigned))

    return FleetPlan(
        tours=fleet_tours,
        unassigned_order_ids=unassigned,
        total_distance_meters=total_distance,
        optimal=False,
    )


def solve_vrp(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    orders: list[tuple[str, str, str]],  # (order_id, pickup_node, dropoff_node)
    cost_matrix: DistanceProvider,
    *,
    brute_force_threshold: int | None = None,
    max_brute_force_shippers: int | None = None,
    max_brute_force_stops_per_tour: int = 6,
    options: RoutingOptions | None = None,
) -> FleetPlan:
    """Solve the VRP: assign orders to shippers and optimize tours.

    For small instances (<= threshold orders AND <= max_shippers shippers),
    uses brute-force for optimality. For larger instances, uses cheapest
    insertion + local search.

    Threshold resolution order:
    1. `options.vrp_brute_force_max_orders` / `options.vrp_brute_force_max_shippers`
    2. `brute_force_threshold` / `max_brute_force_shippers` (explicit override)
    3. `RoutingOptions.DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS` (3) /
       `RoutingOptions.DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS` (2)

    A threshold of 0 disables that side of the brute-force condition.
    """
    if not orders:
        return FleetPlan(
            tours=[(sid, Tour(ordered_stops=[], total_distance_meters=0.0, optimal=True))
                   for sid in shipper_ids],
            unassigned_order_ids=[],
            total_distance_meters=0.0,
            optimal=True,
        )

    order_threshold, shipper_threshold = _resolve_thresholds(
        options, brute_force_threshold, max_brute_force_shippers
    )

    if _is_brute_force_eligible(orders, shipper_ids, order_threshold, shipper_threshold):
        result = _brute_force_vrp(
            shipper_ids,
            shipper_nodes,
            orders,
            cost_matrix,
            max_stops_per_tour=max_brute_force_stops_per_tour,
            options=options,
        )
        if result:
            return result

    return _build_heuristic_fleet(shipper_ids, shipper_nodes, orders, cost_matrix)


def _is_brute_force_eligible(
    orders: list[tuple[str, str, str]],
    shipper_ids: list[str],
    order_threshold: int,
    shipper_threshold: int,
) -> bool:
    """Check whether the instance is small enough for brute-force."""
    return (
        order_threshold > 0
        and len(orders) <= order_threshold
        and shipper_threshold > 0
        and len(shipper_ids) <= shipper_threshold
    )


def _build_assignment_tours(
    shipper_ids: list[str],
    order_ids: list[str],
    order_map: dict[str, tuple[str, str]],
    assignment: tuple[str, ...],
) -> dict[str, list[Stop]] | None:
    """Build tours for a given order-to-shipper assignment; None if invalid."""
    tours_dict: dict[str, list[Stop]] = {sid: [] for sid in shipper_ids}

    for oid, assigned_sid in zip(order_ids, assignment):
        pnode, dnode = order_map[oid]
        tours_dict[assigned_sid].append(Stop(order_id=oid, kind="pickup", node_id=pnode))
        tours_dict[assigned_sid].append(Stop(order_id=oid, kind="dropoff", node_id=dnode))

    for sid in shipper_ids:
        if not _check_precedence(tours_dict[sid]):
            return None
    return tours_dict


def _evaluate_assignment(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    tours_dict: dict[str, list[Stop]],
    cost_matrix: DistanceProvider,
    max_stops_per_tour: int,
    options: RoutingOptions | None,
) -> tuple[float, list[tuple[str, Tour]], bool] | None:
    """Evaluate one assignment; return (total, fleet_tours, all_optimal) or None if invalid."""
    fleet_tours: list[tuple[str, Tour]] = []
    total = 0.0
    all_optimal = True

    for sid in shipper_ids:
        result = _evaluate_single_shipper(
            tours_dict[sid],
            shipper_nodes[sid],
            cost_matrix,
            max_stops_per_tour,
            options,
        )
        if result is None:
            return None
        tour, optimal = result
        total += tour.total_distance_meters
        if not optimal:
            all_optimal = False
        fleet_tours.append((sid, tour))

    return total, fleet_tours, all_optimal


def _evaluate_single_shipper(
    stops: list[Stop],
    shipper_node: str,
    cost_matrix: DistanceProvider,
    max_stops_per_tour: int,
    options: RoutingOptions | None,
) -> tuple[Tour, bool] | None:
    """Evaluate a single shipper's tour; return (tour, optimal) or None if over limit."""
    if len(stops) > max_stops_per_tour:
        return None
    if not stops:
        return Tour(ordered_stops=[], total_distance_meters=0.0, optimal=True), True

    tour = optimize_tour(shipper_node, stops, cost_matrix, options=options)
    return tour, tour.optimal


def _brute_force_vrp(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],
    orders: list[tuple[str, str, str]],
    cost_matrix: DistanceProvider,
    max_stops_per_tour: int = 6,
    options: RoutingOptions | None = None,
) -> FleetPlan | None:
    """Brute-force VRP for small instances.

    Tries all ways to assign orders to shippers, then optimizes each tour.
    Returns FleetPlan with optimal=True if successful.
    """
    order_ids = [oid for oid, _, _ in orders]
    order_map = {oid: (pnode, dnode) for oid, pnode, dnode in orders}

    best_plan: FleetPlan | None = None
    best_total = float("inf")

    for assignment in product(shipper_ids, repeat=len(order_ids)):
        tours_dict = _build_assignment_tours(
            shipper_ids, order_ids, order_map, assignment
        )
        if tours_dict is None:
            continue

        result = _evaluate_assignment(
            shipper_ids,
            shipper_nodes,
            tours_dict,
            cost_matrix,
            max_stops_per_tour,
            options,
        )
        if result is None:
            continue

        total, fleet_tours, all_optimal = result
        if total < best_total:
            best_total = total
            best_plan = FleetPlan(
                tours=fleet_tours,
                unassigned_order_ids=[],
                total_distance_meters=total,
                optimal=all_optimal,
            )

    return best_plan
