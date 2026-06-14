from __future__ import annotations

from app.domain.cost_model import RoutingOptions, edge_cost
from app.infrastructure.graph_loader import ValidatedGraph

Adjacency = dict[str, list[tuple[str, float]]]


def build_directed_adjacency(
    graph: ValidatedGraph, options: RoutingOptions | None = None
) -> Adjacency:
    if options is None:
        options = RoutingOptions()

    adjacency: Adjacency = {node_id: [] for node_id in graph.nodes}

    for idx, edge in enumerate(graph.edges):
        cost = edge_cost(edge.distance, edge.road_type, options)
        if cost == float("inf"):
            continue

        edge_id = f"{edge.from_node}->{edge.to_node}:{idx}"
        if edge_id in options.avoid_edge_ids:
            continue

        _add_neighbor(adjacency, edge.from_node, edge.to_node, cost)
        if not edge.oneway:
            _add_neighbor(adjacency, edge.to_node, edge.from_node, cost)

    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: item[0])

    return adjacency


def build_bidirectional_adjacency(graph: ValidatedGraph) -> Adjacency:
    """Legacy: treats each edge as undirected (backward-compatible)."""
    return build_directed_adjacency(graph, RoutingOptions())


def _add_neighbor(
    adjacency: Adjacency,
    from_node: str,
    to_node: str,
    distance: float,
) -> None:
    neighbors = adjacency[from_node]
    for index, (existing_to, existing_dist) in enumerate(neighbors):
        if existing_to == to_node:
            if distance < existing_dist:
                neighbors[index] = (to_node, distance)
            return
    neighbors.append((to_node, distance))
