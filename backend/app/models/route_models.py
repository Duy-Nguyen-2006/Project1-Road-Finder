from pydantic import BaseModel, Field

from app.models.point import Point


class RoutingOptionsRequest(BaseModel):
    avoid_road_types: list[str] = Field(default_factory=list)
    avoid_edge_ids: list[str] = Field(default_factory=list)
    # Solver thresholds. None (or omitted) means "use the server default".
    # 0 disables the brute-force path entirely (always heuristic).
    tsp_brute_force_max_stops: int | None = Field(default=None, ge=0)
    vrp_brute_force_max_orders: int | None = Field(default=None, ge=0)
    vrp_brute_force_max_shippers: int | None = Field(default=None, ge=0)


class GraphBoundsResponse(BaseModel):
    bbox: dict[str, float]
    # Informational metadata from the graph file; snap_service does not enforce this.
    max_snap_distance_meters: float
    graph_version: str


class RouteRequest(BaseModel):
    """POST /route request body."""
    start: Point
    end: Point
    options: RoutingOptionsRequest = Field(default_factory=RoutingOptionsRequest)


class RouteResponse(BaseModel):
    """POST /route response body."""
    route_points: list[Point]
    distance: float = Field(ge=0)


# --- Phase 2: Assignment & Tour DTOs ---


class OrderRequest(BaseModel):
    id: str
    pickup: Point
    dropoff: Point


class ShipperRequest(BaseModel):
    id: str
    location: Point


class LegResponse(BaseModel):
    kind: str
    distance_meters: float
    route_points: list[Point]


class ShipperRouteResponse(BaseModel):
    shipper_id: str
    feasible: bool
    total_distance_meters: float
    legs: list[LegResponse]


class AssignmentRequest(BaseModel):
    order: OrderRequest
    shippers: list[ShipperRequest]
    options: RoutingOptionsRequest = Field(default_factory=RoutingOptionsRequest)


class AssignmentResponse(BaseModel):
    recommended_shipper_id: str | None
    ranking: list[ShipperRouteResponse]


class StopResponse(BaseModel):
    order_id: str
    kind: str
    coordinate: Point


class TourRequest(BaseModel):
    shipper: ShipperRequest
    orders: list[OrderRequest]
    options: RoutingOptionsRequest = Field(default_factory=RoutingOptionsRequest)


class TourResponse(BaseModel):
    shipper_id: str
    ordered_stops: list[StopResponse]
    legs: list[LegResponse]
    total_distance_meters: float
    optimal: bool
    feasible: bool = True


# --- Phase 3: VRP Fleet DTOs ---


class FleetRequest(BaseModel):
    shippers: list[ShipperRequest]
    orders: list[OrderRequest]
    options: RoutingOptionsRequest = Field(default_factory=RoutingOptionsRequest)


class FleetResponse(BaseModel):
    tours: list[TourResponse]
    unassigned_order_ids: list[str]
    total_distance_meters: float
    optimal: bool
