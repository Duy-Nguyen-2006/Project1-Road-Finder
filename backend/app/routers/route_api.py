from fastapi import APIRouter, Request

from app.application.cost_matrix import CostMatrix
from app.application.graph_bounds import build_graph_bounds_payload
from app.application.health import build_health_payload
from app.domain.assignment import rank_shippers_for_order
from app.domain.cost_model import RoutingOptions
from app.domain.errors import AcceptedAreaError, NoRouteError
from app.application.node_lookup import GraphNodeLookup
from app.application.snap_service import snap_point
from app.domain.tsp import Stop, optimize_tour
from app.domain.vrp import solve_vrp
from app.http.route_errors import http_exception_for_domain_error
from app.models.point import Point
from app.models.route_models import (
    AssignmentRequest,
    AssignmentResponse,
    FleetRequest,
    FleetResponse,
    FleetTourResponse,
    GraphBoundsResponse,
    RouteRequest,
    RouteResponse,
    ShipperRouteResponse,
    StopResponse,
    TourRequest,
    TourResponse,
)
from app.services.route_computation import compute_shortest_path_response
from app.services.tour_response_builder import (
    build_assignment_leg,
    build_tour_legs,
)

router = APIRouter()


def _runtime(request: Request):
    return request.app.state.graph_runtime


def _to_routing_options(options_req) -> RoutingOptions:
    return RoutingOptions(
        avoid_road_types=tuple(options_req.avoid_road_types),
        avoid_edge_ids=tuple(options_req.avoid_edge_ids),
        tsp_brute_force_max_stops=options_req.tsp_brute_force_max_stops,
        vrp_brute_force_max_orders=options_req.vrp_brute_force_max_orders,
        vrp_brute_force_max_shippers=options_req.vrp_brute_force_max_shippers,
    )


@router.get("/health")
def health_check(request: Request) -> dict:
    return build_health_payload(_runtime(request))


@router.get("/graph/bounds")
def graph_bounds(request: Request) -> GraphBoundsResponse:
    payload = build_graph_bounds_payload(_runtime(request))
    return GraphBoundsResponse(**payload)


@router.post("/route")
def route(request: Request, body: RouteRequest) -> RouteResponse:
    options = _to_routing_options(body.options)
    try:
        result = compute_shortest_path_response(
            _runtime(request), body.start, body.end, options
        )
    except (AcceptedAreaError, NoRouteError) as exc:
        raise http_exception_for_domain_error(exc) from exc
    return RouteResponse(
        route_points=result.route_points,
        distance=result.distance,
    )


@router.post("/assignments")
def assignments(request: Request, body: AssignmentRequest) -> AssignmentResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        cost_matrix = CostMatrix(runtime, options)

        lookup = GraphNodeLookup(runtime.nodes)
        shipper_nodes = {}
        shipper_snaps = {}
        for s in body.shippers:
            snap = snap_point(runtime, s.location.latitude, s.location.longitude)
            shipper_nodes[s.id] = snap.node_id
            shipper_snaps[s.id] = (snap, (s.location.latitude, s.location.longitude))

        pickup_snap = snap_point(runtime, body.order.pickup.latitude, body.order.pickup.longitude)
        dropoff_snap = snap_point(runtime, body.order.dropoff.latitude, body.order.dropoff.longitude)
        pickup_click = (body.order.pickup.latitude, body.order.pickup.longitude)
        dropoff_click = (body.order.dropoff.latitude, body.order.dropoff.longitude)

        # Pre-compute distances
        all_nodes = list(shipper_nodes.values()) + [pickup_snap.node_id, dropoff_snap.node_id]
        cost_matrix.compute_for_nodes(all_nodes)

        # Rank shippers
        result = rank_shippers_for_order(
            shipper_ids=[s.id for s in body.shippers],
            shipper_nodes=shipper_nodes,
            pickup_node=pickup_snap.node_id,
            dropoff_node=dropoff_snap.node_id,
            cost_matrix=cost_matrix,
        )

        # Build response
        ranking = []
        for sr in result.ranking:
            legs = []
            if sr.feasible and len(sr.legs) == 2:
                snap, shipper_click = shipper_snaps[sr.shipper_id]
                (_, path_pickup, dist_pickup) = sr.legs[0]
                (_, path_drop, dist_drop) = sr.legs[1]
                legs.append(
                    build_assignment_leg(
                        lookup,
                        clicked_start=shipper_click,
                        start_snap_distance_meters=snap.distance_meters,
                        clicked_end=pickup_click,
                        end_snap_distance_meters=pickup_snap.distance_meters,
                        path_node_ids=path_pickup,
                        graph_distance_meters=dist_pickup,
                        kind="to_pickup",
                    )
                )
                legs.append(
                    build_assignment_leg(
                        lookup,
                        clicked_start=pickup_click,
                        start_snap_distance_meters=pickup_snap.distance_meters,
                        clicked_end=dropoff_click,
                        end_snap_distance_meters=dropoff_snap.distance_meters,
                        path_node_ids=path_drop,
                        graph_distance_meters=dist_drop,
                        kind="to_dropoff",
                    )
                )
            total_m = (
                sum(leg.distance_meters for leg in legs)
                if legs
                else sr.total_distance_meters
            )
            ranking.append(ShipperRouteResponse(
                shipper_id=sr.shipper_id,
                feasible=sr.feasible,
                total_distance_meters=total_m,
                legs=legs,
            ))

        return AssignmentResponse(
            recommended_shipper_id=result.recommended_shipper_id,
            ranking=ranking,
        )
    except AcceptedAreaError as exc:
        raise http_exception_for_domain_error(exc) from exc


@router.post("/tours")
def tours(request: Request, body: TourRequest) -> TourResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        lookup = GraphNodeLookup(runtime.nodes)
        cost_matrix = CostMatrix(runtime, options)

        shipper_snap = snap_point(runtime, body.shipper.location.latitude, body.shipper.location.longitude)
        shipper_click = (body.shipper.location.latitude, body.shipper.location.longitude)

        stops: list[Stop] = []
        stop_coordinates: dict[tuple[str, str], tuple[float, float]] = {}
        stop_snap_distances: dict[tuple[str, str], float] = {}
        all_nodes = [shipper_snap.node_id]
        for order in body.orders:
            pickup_snap = snap_point(runtime, order.pickup.latitude, order.pickup.longitude)
            dropoff_snap = snap_point(runtime, order.dropoff.latitude, order.dropoff.longitude)
            stops.append(Stop(order_id=order.id, kind="pickup", node_id=pickup_snap.node_id))
            stops.append(Stop(order_id=order.id, kind="dropoff", node_id=dropoff_snap.node_id))
            stop_coordinates[(order.id, "pickup")] = (order.pickup.latitude, order.pickup.longitude)
            stop_coordinates[(order.id, "dropoff")] = (order.dropoff.latitude, order.dropoff.longitude)
            stop_snap_distances[(order.id, "pickup")] = pickup_snap.distance_meters
            stop_snap_distances[(order.id, "dropoff")] = dropoff_snap.distance_meters
            all_nodes.extend([pickup_snap.node_id, dropoff_snap.node_id])

        # Pre-compute distances
        cost_matrix.compute_for_nodes(all_nodes)

        # Optimize tour
        tour = optimize_tour(shipper_snap.node_id, stops, cost_matrix, options=options)

        # Build response
        ordered_stops = []
        for stop in tour.ordered_stops:
            node = runtime.nodes[stop.node_id]
            ordered_stops.append(StopResponse(
                order_id=stop.order_id,
                kind=stop.kind,
                coordinate=Point(latitude=node.latitude, longitude=node.longitude),
            ))

        legs = build_tour_legs(
            lookup,
            shipper_click=shipper_click,
            shipper_snap_distance_meters=shipper_snap.distance_meters,
            shipper_node_id=shipper_snap.node_id,
            ordered_stops=tour.ordered_stops,
            stop_coordinates=stop_coordinates,
            stop_snap_distances=stop_snap_distances,
            cost_matrix=cost_matrix,
        )

        return TourResponse(
            shipper_id=body.shipper.id,
            ordered_stops=ordered_stops,
            legs=legs,
            total_distance_meters=tour.total_distance_meters,
            optimal=tour.optimal,
        )
    except AcceptedAreaError as exc:
        raise http_exception_for_domain_error(exc) from exc


@router.post("/fleet")
def fleet(request: Request, body: FleetRequest) -> FleetResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        lookup = GraphNodeLookup(runtime.nodes)
        cost_matrix = CostMatrix(runtime, options)

        shipper_nodes = {}
        shipper_snaps: dict[str, tuple] = {}
        for s in body.shippers:
            snap = snap_point(runtime, s.location.latitude, s.location.longitude)
            shipper_nodes[s.id] = snap.node_id
            shipper_snaps[s.id] = (snap, (s.location.latitude, s.location.longitude))

        orders_data = []
        stop_coordinates: dict[tuple[str, str], tuple[float, float]] = {}
        stop_snap_distances: dict[tuple[str, str], float] = {}
        all_nodes = list(shipper_nodes.values())
        for order in body.orders:
            pickup_snap = snap_point(runtime, order.pickup.latitude, order.pickup.longitude)
            dropoff_snap = snap_point(runtime, order.dropoff.latitude, order.dropoff.longitude)
            orders_data.append((order.id, pickup_snap.node_id, dropoff_snap.node_id))
            stop_coordinates[(order.id, "pickup")] = (order.pickup.latitude, order.pickup.longitude)
            stop_coordinates[(order.id, "dropoff")] = (order.dropoff.latitude, order.dropoff.longitude)
            stop_snap_distances[(order.id, "pickup")] = pickup_snap.distance_meters
            stop_snap_distances[(order.id, "dropoff")] = dropoff_snap.distance_meters
            all_nodes.extend([pickup_snap.node_id, dropoff_snap.node_id])

        # Pre-compute distances
        cost_matrix.compute_for_nodes(all_nodes)

        # Solve VRP
        plan = solve_vrp(
            shipper_ids=[s.id for s in body.shippers],
            shipper_nodes=shipper_nodes,
            orders=orders_data,
            cost_matrix=cost_matrix,
            options=options,
        )

        # Build response
        tours = []
        for sid, tour in plan.tours:
            ordered_stops = []
            for stop in tour.ordered_stops:
                node = runtime.nodes[stop.node_id]
                ordered_stops.append(StopResponse(
                    order_id=stop.order_id,
                    kind=stop.kind,
                    coordinate=Point(latitude=node.latitude, longitude=node.longitude),
                ))

            snap, shipper_click = shipper_snaps[sid]
            legs = build_tour_legs(
                lookup,
                shipper_click=shipper_click,
                shipper_snap_distance_meters=snap.distance_meters,
                shipper_node_id=shipper_nodes[sid],
                ordered_stops=tour.ordered_stops,
                stop_coordinates=stop_coordinates,
                stop_snap_distances=stop_snap_distances,
                cost_matrix=cost_matrix,
            )

            tours.append(FleetTourResponse(
                shipper_id=sid,
                ordered_stops=ordered_stops,
                legs=legs,
                total_distance_meters=tour.total_distance_meters,
                optimal=tour.optimal,
            ))

        return FleetResponse(
            tours=tours,
            unassigned_order_ids=plan.unassigned_order_ids,
            total_distance_meters=plan.total_distance_meters,
            optimal=plan.optimal,
        )
    except AcceptedAreaError as exc:
        raise http_exception_for_domain_error(exc) from exc
