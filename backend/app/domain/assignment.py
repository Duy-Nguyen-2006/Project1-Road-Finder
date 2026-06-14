from __future__ import annotations

from dataclasses import dataclass

from app.domain.protocols import DistanceProvider


@dataclass(frozen=True)
class ShipperRoute:
    shipper_id: str
    legs: list[tuple[str, list[str], float]]  # (kind, path_node_ids, distance)
    total_distance_meters: float
    feasible: bool


@dataclass(frozen=True)
class AssignmentResult:
    recommended_shipper_id: str | None
    ranking: list[ShipperRoute]


def rank_shippers_for_order(
    shipper_ids: list[str],
    shipper_nodes: dict[str, str],  # shipper_id -> node_id
    pickup_node: str,
    dropoff_node: str,
    cost_matrix: DistanceProvider,
) -> AssignmentResult:
    """Rank shippers by total distance for a single order.

    For each shipper: total = SP(shipper→pickup) + SP(pickup→dropoff)
    Returns sorted by total distance, tie-break by shipper_id.
    """
    routes: list[ShipperRoute] = []

    for sid in shipper_ids:
        snode = shipper_nodes[sid]

        dist_to_pickup = cost_matrix.get_distance(snode, pickup_node)
        dist_pickup_to_dropoff = cost_matrix.get_distance(pickup_node, dropoff_node)

        if dist_to_pickup is None or dist_pickup_to_dropoff is None:
            routes.append(ShipperRoute(
                shipper_id=sid,
                legs=[],
                total_distance_meters=float("inf"),
                feasible=False,
            ))
            continue

        if dist_to_pickup == float("inf") or dist_pickup_to_dropoff == float("inf"):
            routes.append(ShipperRoute(
                shipper_id=sid,
                legs=[],
                total_distance_meters=float("inf"),
                feasible=False,
            ))
            continue

        total = dist_to_pickup + dist_pickup_to_dropoff
        path_to_pickup = cost_matrix.get_path(snode, pickup_node) or []
        path_to_dropoff = cost_matrix.get_path(pickup_node, dropoff_node) or []

        legs = [
            ("to_pickup", path_to_pickup, dist_to_pickup),
            ("to_dropoff", path_to_dropoff, dist_pickup_to_dropoff),
        ]

        routes.append(ShipperRoute(
            shipper_id=sid,
            legs=legs,
            total_distance_meters=total,
            feasible=True,
        ))

    # Sort: feasible first, then by total distance, tie-break by shipper_id
    routes.sort(key=lambda r: (not r.feasible, r.total_distance_meters, r.shipper_id))

    recommended = None
    for r in routes:
        if r.feasible:
            recommended = r.shipper_id
            break

    return AssignmentResult(
        recommended_shipper_id=recommended,
        ranking=routes,
    )
