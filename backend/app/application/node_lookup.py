from __future__ import annotations

from dataclasses import dataclass

from app.domain.graph_types import GraphNode


@dataclass(frozen=True)
class GraphNodeLookup:
    nodes: dict[str, GraphNode]

    def node_coordinate(self, node_id: str) -> tuple[float, float]:
        node = self.nodes[node_id]
        return (node.latitude, node.longitude)
