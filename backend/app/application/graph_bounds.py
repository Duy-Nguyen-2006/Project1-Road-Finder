from __future__ import annotations

from typing import Any

from app.application.graph_runtime import GraphRuntime


def build_graph_bounds_payload(runtime: GraphRuntime) -> dict[str, Any]:
    bbox = runtime.metadata.bbox
    return {
        "bbox": {
            "min_latitude": bbox.min_latitude,
            "min_longitude": bbox.min_longitude,
            "max_latitude": bbox.max_latitude,
            "max_longitude": bbox.max_longitude,
        },
        "max_snap_distance_meters": runtime.metadata.max_snap_distance_meters,
        "graph_version": runtime.metadata.graph_version,
    }
