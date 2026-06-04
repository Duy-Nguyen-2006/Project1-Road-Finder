from __future__ import annotations

from app.infrastructure.graph_loader import ValidatedGraph

Adjacency = dict[str, list[tuple[str, float]]]


def build_bidirectional_adjacency(graph: ValidatedGraph) -> Adjacency:
    """MVP treats each directed edge record as an undirected link with the same weight."""
    adjacency: Adjacency = {node_id: [] for node_id in graph.nodes}

    for edge in graph.edges:
        _add_neighbor(adjacency, edge.from_node, edge.to_node, edge.distance)
        _add_neighbor(adjacency, edge.to_node, edge.from_node, edge.distance)

    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: item[0])

    return adjacency


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
