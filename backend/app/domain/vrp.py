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
    # shipper_id -> list of stops
    tours: dict[str, list[Stop]] = {sid: [] for sid in shipper_ids}

    # Sort orders by some heuristic (e.g., distance from center)
    for order_id, pickup_node, dropoff_node in orders:
        best_shipper = None
        best_position = -1
        best_cost_increase = float("inf")

        for sid in shipper_ids:
            snode = shipper_nodes[sid]
            current_stops = tours[sid]
            old_cost = _compute_tour_distance(snode, current_stops, cost_matrix)

            # Try all valid insertion positions for pickup and dropoff
            # Constraint: pickup must come before dropoff
            pickup_stop = Stop(order_id=order_id, kind="pickup", node_id=pickup_node)
            dropoff_stop = Stop(order_id=order_id, kind="dropoff", node_id=dropoff_node)

            for pickup_pos in range(len(current_stops) + 1):
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

                    if increase < best_cost_increase:
                        best_cost_increase = increase
                        best_shipper = sid
                        best_position = (pickup_pos, dropoff_pos)

        if best_shipper is not None:
            pickup_stop = Stop(order_id=order_id, kind="pickup", node_id=pickup_node)
            dropoff_stop = Stop(order_id=order_id, kind="dropoff", node_id=dropoff_node)
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

    improved = True
    current = list(stops)
    current_dist = _compute_tour_distance(shipper_node, current, cost_matrix)

    while improved:
        improved = False
        for i in range(len(current) - 1):
            for j in range(i + 2, len(current)):
                candidate = current[:i + 1] + current[i + 1:j + 1][::-1] + current[j + 1:]
                if not _check_precedence(candidate):
                    continue

                new_dist = _compute_tour_distance(shipper_node, candidate, cost_matrix)
                if new_dist < current_dist:
                    current = candidate
                    current_dist = new_dist
                    improved = True
                    break
            if improved:
                break
    return current


def _inter_route_relocate(
    tours: dict[str, list[Stop]],
    shipper_nodes: dict[str, str],
    cost_matrix: DistanceProvider,
) -> dict[str, list[Stop]]:
    """Try relocating an order from one shipper to another."""
    improved = True
    current = dict(tours)

    while improved:
        improved = False
        for src_sid in list(current.keys()):
            src_stops = current[src_sid]
            if len(src_stops) < 2:
                continue

            # Find orders in this tour
            orders_in_tour: dict[str, list[int]] = {}
            for idx, stop in enumerate(src_stops):
                orders_in_tour.setdefault(stop.order_id, []).append(idx)

            for order_id, indices in orders_in_tour.items():
                if len(indices) != 2:
                    continue

                pickup_idx, dropoff_idx = min(indices), max(indices)

                # Try moving to each other shipper
                for dst_sid in current.keys():
                    if dst_sid == src_sid:
                        continue

                    # Remove from source
                    new_src = [s for s in src_stops if s.order_id != order_id]
                    pickup_stop = src_stops[pickup_idx]
                    dropoff_stop = src_stops[dropoff_idx]

                    # Try cheapest insertion into destination
                    dst_stops = current[dst_sid]
                    best_insert = None
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

                            new_dst_cost = _compute_tour_distance(
                                shipper_nodes[dst_sid], candidate, cost_matrix
                            )
                            if new_dst_cost < best_cost:
                                best_cost = new_dst_cost
                                best_insert = candidate

                    if best_insert is None:
                        continue

                    # Compute total before and after
                    old_total = (
                        _compute_tour_distance(shipper_nodes[src_sid], src_stops, cost_matrix)
                        + _compute_tour_distance(shipper_nodes[dst_sid], dst_stops, cost_matrix)
                    )
                    new_total = (
                        _compute_tour_distance(shipper_nodes[src_sid], new_src, cost_matrix)
                        + best_cost
                    )

                    if new_total < old_total:
                        current[src_sid] = new_src
                        current[dst_sid] = best_insert
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

    return current


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

    For small instances (≤ threshold orders AND ≤ max_shippers shippers),
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

    # Resolve thresholds: options > explicit kwargs > defaults
    if options is not None:
        order_threshold = options.resolved_vrp_order_threshold()
        shipper_threshold = options.resolved_vrp_shipper_threshold()
    else:
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

    # Check if small enough for brute-force
    if order_threshold > 0 and len(orders) <= order_threshold \
            and shipper_threshold > 0 and len(shipper_ids) <= shipper_threshold:
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

    # Heuristic: cheapest insertion + local search
    tours_dict = _cheapest_insertion(shipper_ids, shipper_nodes, orders, cost_matrix)

    # Local search: intra-route 2-opt
    for sid in shipper_ids:
        tours_dict[sid] = _intra_route_2opt(
            tours_dict[sid], cost_matrix, shipper_nodes[sid]
        )

    # Local search: inter-route relocate
    tours_dict = _inter_route_relocate(tours_dict, shipper_nodes, cost_matrix)

    # Build result
    fleet_tours = []
    total_distance = 0.0
    assigned_orders = set()
    unassigned_from_inf: set[str] = set()

    for sid in shipper_ids:
        stops = tours_dict[sid]
        dist = _compute_tour_distance(shipper_nodes[sid], stops, cost_matrix)
        if dist == float("inf"):
            for stop in stops:
                unassigned_from_inf.add(stop.order_id)
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
        for stop in stops:
            assigned_orders.add(stop.order_id)

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

    # Generate all possible assignments of orders to shippers
    # Each order can go to any shipper
    best_plan = None
    best_total = float("inf")

    for assignment in product(shipper_ids, repeat=len(order_ids)):
        # Build tours for this assignment
        tours_dict: dict[str, list[Stop]] = {sid: [] for sid in shipper_ids}

        for oid, assigned_sid in zip(order_ids, assignment):
            pnode, dnode = order_map[oid]
            tours_dict[assigned_sid].append(Stop(order_id=oid, kind="pickup", node_id=pnode))
            tours_dict[assigned_sid].append(Stop(order_id=oid, kind="dropoff", node_id=dnode))

        # Check precedence for each tour
        valid = True
        for sid in shipper_ids:
            if not _check_precedence(tours_dict[sid]):
                valid = False
                break
        if not valid:
            continue

        for sid in shipper_ids:
            if len(tours_dict[sid]) > max_stops_per_tour:
                valid = False
                break
        if not valid:
            continue

        total = 0.0
        fleet_tours = []
        all_optimal = True

        for sid in shipper_ids:
            stops = tours_dict[sid]
            if not stops:
                fleet_tours.append((sid, Tour(
                    ordered_stops=[],
                    total_distance_meters=0.0,
                    optimal=True,
                )))
                continue

            tour = optimize_tour(shipper_nodes[sid], stops, cost_matrix, options=options)
            if not tour.optimal:
                all_optimal = False
            total += tour.total_distance_meters
            fleet_tours.append((sid, tour))

        if total < best_total:
            best_total = total
            best_plan = FleetPlan(
                tours=fleet_tours,
                unassigned_order_ids=[],
                total_distance_meters=total,
                optimal=all_optimal,
            )

    return best_plan
