from fastapi import APIRouter, HTTPException, Request

from app.application.cost_matrix import CostMatrix
from app.application.graph_bounds import build_graph_bounds_payload
from app.application.health import build_health_payload
from app.domain.assignment import rank_shippers_for_order
from app.domain.cost_model import RoutingOptions
from app.domain.errors import AcceptedAreaError, NoRouteError
from app.domain.snapper import snap_point
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
    LegResponse,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    RouteRequest,
    RouteResponse,
    ShipperRouteResponse,
    ShortestPathRequest,
    ShortestPathResponse,
    StopResponse,
    TourRequest,
    TourResponse,
)
from app.services.route_computation import compute_shortest_path_response

router = APIRouter()


def _runtime(request: Request):
    return request.app.state.graph_runtime


def _to_routing_options(options_req) -> RoutingOptions:
    return RoutingOptions(
        avoid_road_types=tuple(options_req.avoid_road_types),
        avoid_edge_ids=tuple(options_req.avoid_edge_ids),
    )


@router.get("/health")
def health_check(request: Request) -> dict:
    return build_health_payload(_runtime(request))


@router.get("/graph-bounds", response_model=GraphBoundsResponse)
def graph_bounds_legacy(request: Request) -> GraphBoundsResponse:
    """Legacy endpoint. Use GET /graph/bounds instead."""
    payload = build_graph_bounds_payload(_runtime(request))
    return GraphBoundsResponse(**payload)


@router.get("/graph/bounds", response_model=GraphBoundsResponse)
def graph_bounds(request: Request) -> GraphBoundsResponse:
    payload = build_graph_bounds_payload(_runtime(request))
    return GraphBoundsResponse(**payload)


@router.post("/route", response_model=RouteResponse)
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


@router.post("/assignments", response_model=AssignmentResponse)
def assignments(request: Request, body: AssignmentRequest) -> AssignmentResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        cost_matrix = CostMatrix(runtime, options)

        # Snap all points
        shipper_nodes = {}
        for s in body.shippers:
            snap = snap_point(runtime, s.location.latitude, s.location.longitude)
            shipper_nodes[s.id] = snap.node_id

        pickup_snap = snap_point(runtime, body.order.pickup.latitude, body.order.pickup.longitude)
        dropoff_snap = snap_point(runtime, body.order.dropoff.latitude, body.order.dropoff.longitude)

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
            for kind, path_nodes, dist in sr.legs:
                route_points = []
                for nid in path_nodes:
                    node = runtime.nodes[nid]
                    route_points.append(Point(latitude=node.latitude, longitude=node.longitude))
                legs.append(LegResponse(
                    kind=kind,
                    distance_meters=dist,
                    route_points=route_points,
                ))
            ranking.append(ShipperRouteResponse(
                shipper_id=sr.shipper_id,
                feasible=sr.feasible,
                total_distance_meters=sr.total_distance_meters,
                legs=legs,
            ))

        return AssignmentResponse(
            recommended_shipper_id=result.recommended_shipper_id,
            ranking=ranking,
        )
    except AcceptedAreaError as exc:
        raise http_exception_for_domain_error(exc) from exc


@router.post("/tours", response_model=TourResponse)
def tours(request: Request, body: TourRequest) -> TourResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        cost_matrix = CostMatrix(runtime, options)

        # Snap shipper location
        shipper_snap = snap_point(runtime, body.shipper.location.latitude, body.shipper.location.longitude)

        # Build stops for each order
        stops: list[Stop] = []
        all_nodes = [shipper_snap.node_id]
        for order in body.orders:
            pickup_snap = snap_point(runtime, order.pickup.latitude, order.pickup.longitude)
            dropoff_snap = snap_point(runtime, order.dropoff.latitude, order.dropoff.longitude)
            stops.append(Stop(order_id=order.id, kind="pickup", node_id=pickup_snap.node_id))
            stops.append(Stop(order_id=order.id, kind="dropoff", node_id=dropoff_snap.node_id))
            all_nodes.extend([pickup_snap.node_id, dropoff_snap.node_id])

        # Pre-compute distances
        cost_matrix.compute_for_nodes(all_nodes)

        # Optimize tour
        tour = optimize_tour(shipper_snap.node_id, stops, cost_matrix)

        # Build response
        ordered_stops = []
        for stop in tour.ordered_stops:
            node = runtime.nodes[stop.node_id]
            ordered_stops.append(StopResponse(
                order_id=stop.order_id,
                kind=stop.kind,
                coordinate=Point(latitude=node.latitude, longitude=node.longitude),
            ))

        # Build legs
        legs = []
        current = shipper_snap.node_id
        for stop in tour.ordered_stops:
            dist = cost_matrix.get_distance(current, stop.node_id)
            path = cost_matrix.get_path(current, stop.node_id) or []
            route_points = [
                Point(latitude=runtime.nodes[nid].latitude, longitude=runtime.nodes[nid].longitude)
                for nid in path
            ]
            legs.append(LegResponse(
                kind=f"{stop.order_id}_{stop.kind}",
                distance_meters=dist or 0.0,
                route_points=route_points,
            ))
            current = stop.node_id

        return TourResponse(
            shipper_id=body.shipper.id,
            ordered_stops=ordered_stops,
            legs=legs,
            total_distance_meters=tour.total_distance_meters,
            optimal=tour.optimal,
        )
    except AcceptedAreaError as exc:
        raise http_exception_for_domain_error(exc) from exc


@router.post("/fleet", response_model=FleetResponse)
def fleet(request: Request, body: FleetRequest) -> FleetResponse:
    runtime = _runtime(request)
    options = _to_routing_options(body.options)

    try:
        cost_matrix = CostMatrix(runtime, options)

        # Snap all points
        shipper_nodes = {}
        for s in body.shippers:
            snap = snap_point(runtime, s.location.latitude, s.location.longitude)
            shipper_nodes[s.id] = snap.node_id

        orders_data = []
        all_nodes = list(shipper_nodes.values())
        for order in body.orders:
            pickup_snap = snap_point(runtime, order.pickup.latitude, order.pickup.longitude)
            dropoff_snap = snap_point(runtime, order.dropoff.latitude, order.dropoff.longitude)
            orders_data.append((order.id, pickup_snap.node_id, dropoff_snap.node_id))
            all_nodes.extend([pickup_snap.node_id, dropoff_snap.node_id])

        # Pre-compute distances
        cost_matrix.compute_for_nodes(all_nodes)

        # Solve VRP
        plan = solve_vrp(
            shipper_ids=[s.id for s in body.shippers],
            shipper_nodes=shipper_nodes,
            orders=orders_data,
            cost_matrix=cost_matrix,
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

            legs = []
            current = shipper_nodes[sid]
            for stop in tour.ordered_stops:
                dist = cost_matrix.get_distance(current, stop.node_id)
                path = cost_matrix.get_path(current, stop.node_id) or []
                route_points = [
                    Point(latitude=runtime.nodes[nid].latitude, longitude=runtime.nodes[nid].longitude)
                    for nid in path
                ]
                legs.append(LegResponse(
                    kind=f"{stop.order_id}_{stop.kind}",
                    distance_meters=dist or 0.0,
                    route_points=route_points,
                ))
                current = stop.node_id

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


@router.post("/shortest-path", response_model=ShortestPathResponse)
def shortest_path(
    request: Request, body: ShortestPathRequest
) -> ShortestPathResponse:
    try:
        return compute_shortest_path_response(
            _runtime(request), body.start, body.end
        )
    except (AcceptedAreaError, NoRouteError) as exc:
        raise http_exception_for_domain_error(exc) from exc


@router.post("/optimize-route", response_model=OptimizeRouteResponse)
def optimize_route(
    request: Request, body: OptimizeRouteRequest
) -> OptimizeRouteResponse:
    if len(body.points) != 2:
        raise HTTPException(
            status_code=422,
            detail="optimize-route requires exactly two points",
        )
    try:
        result = compute_shortest_path_response(
            _runtime(request), body.points[0], body.points[1]
        )
    except (AcceptedAreaError, NoRouteError) as exc:
        raise http_exception_for_domain_error(exc) from exc
    return OptimizeRouteResponse(
        route_points=result.route_points,
        distance=result.distance,
        start_node_id=result.start_node_id,
        end_node_id=result.end_node_id,
    )
