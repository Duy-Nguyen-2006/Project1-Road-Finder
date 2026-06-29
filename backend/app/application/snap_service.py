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
    """Snap a clicked point to the nearest graph node.

    The only accepted-area constraint is the bbox. The previous
    max-snap-distance check (200m) was removed because it made the
    fixture graph (6 nodes spread over a 22km x 33km bbox) almost
    unusable: the user could only click within a tiny radius around
    one of the few nodes. The route leg already includes the snap
    distance, so a long snap just shows up as a longer leg.
    """
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

    return SnapResult(node_id=node_id, distance_meters=distance_meters)
