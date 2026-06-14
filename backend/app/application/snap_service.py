from __future__ import annotations

from dataclasses import dataclass

from app.application.graph_runtime import GraphRuntime
from app.domain.errors import AcceptedAreaError
from app.utils.distance import haversine_meters


@dataclass(frozen=True)
class SnapResult:
    node_id: str
    distance_meters: float


def _is_inside_bbox(runtime: GraphRuntime, latitude: float, longitude: float) -> bool:
    bbox = runtime.metadata.bbox
    return (
        bbox.min_latitude <= latitude <= bbox.max_latitude
        and bbox.min_longitude <= longitude <= bbox.max_longitude
    )


def snap_point(
    runtime: GraphRuntime, latitude: float, longitude: float
) -> SnapResult:
    if not _is_inside_bbox(runtime, latitude, longitude):
        raise AcceptedAreaError()

    node_id = runtime.grid_index.nearest_node_id(latitude, longitude)
    if not node_id:
        raise AcceptedAreaError()

    node = runtime.nodes[node_id]
    distance_meters = haversine_meters(
        latitude,
        longitude,
        node.latitude,
        node.longitude,
    )
    if distance_meters > runtime.metadata.max_snap_distance_meters:
        raise AcceptedAreaError()

    return SnapResult(node_id=node_id, distance_meters=distance_meters)
