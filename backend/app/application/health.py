from __future__ import annotations

from typing import Any

from app.application.graph_runtime import GraphRuntime


def build_health_payload(runtime: GraphRuntime) -> dict[str, Any]:
    return {
        "status": "ok",
        "graph": {
            "loaded": True,
            "graph_version": runtime.metadata.graph_version,
            "node_count": runtime.node_count,
            "edge_count": runtime.edge_count,
        },
        "cache": {
            "route_cache_size": runtime.route_cache.size,
            "route_cache_limit": runtime.route_cache.limit,
        },
    }
