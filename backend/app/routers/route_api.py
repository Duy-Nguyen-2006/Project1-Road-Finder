from fastapi import APIRouter, HTTPException, Request

from app.application.graph_bounds import build_graph_bounds_payload
from app.application.health import build_health_payload
from app.domain.errors import AcceptedAreaError, NoRouteError
from app.http.route_errors import http_exception_for_domain_error
from app.models.route_models import (
    GraphBoundsResponse,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    ShortestPathRequest,
    ShortestPathResponse,
)
from app.services.route_computation import compute_shortest_path_response

router = APIRouter()


def _runtime(request: Request):
    return request.app.state.graph_runtime


@router.get("/health")
def health_check(request: Request) -> dict:
    return build_health_payload(_runtime(request))


@router.get("/graph-bounds", response_model=GraphBoundsResponse)
def graph_bounds(request: Request) -> GraphBoundsResponse:
    payload = build_graph_bounds_payload(_runtime(request))
    return GraphBoundsResponse(**payload)


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
