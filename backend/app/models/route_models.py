from pydantic import BaseModel, Field

from app.models.point import Point


class ShortestPathRequest(BaseModel):
    start: Point
    end: Point


class ShortestPathResponse(BaseModel):
    route_points: list[Point]
    distance: float = Field(gt=0)
    start_node_id: str
    end_node_id: str


class GraphBoundsResponse(BaseModel):
    bbox: dict[str, float]
    max_snap_distance_meters: float
    graph_version: str


class OptimizeRouteRequest(BaseModel):
    points: list[Point]


class OptimizeRouteResponse(BaseModel):
    route_points: list[Point]
    distance: float = Field(gt=0)
    start_node_id: str
    end_node_id: str
