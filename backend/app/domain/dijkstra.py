from __future__ import annotations

import heapq
from dataclasses import dataclass

from app.domain.errors import NoRouteError
from app.domain.graph import Adjacency, build_reverse_adjacency

_INF = float("inf")


@dataclass(frozen=True)
class DijkstraResult:
    node_ids: list[str]
    graph_distance_meters: float


def bidirectional_dijkstra(
    adjacency: Adjacency,
    start_node_id: str,
    end_node_id: str,
    reverse_adjacency: Adjacency | None = None,
) -> DijkstraResult:
    if start_node_id not in adjacency or end_node_id not in adjacency:
        raise NoRouteError()

    if start_node_id == end_node_id:
        return DijkstraResult(node_ids=[start_node_id], graph_distance_meters=0.0)

    if reverse_adjacency is None:
        reverse_adjacency = build_reverse_adjacency(adjacency)

    dist_f: dict[str, float] = {start_node_id: 0.0}
    dist_b: dict[str, float] = {end_node_id: 0.0}
    parent_f: dict[str, str | None] = {start_node_id: None}
    parent_b: dict[str, str | None] = {end_node_id: None}

    heap_f: list[tuple[float, str]] = [(0.0, start_node_id)]
    heap_b: list[tuple[float, str]] = [(0.0, end_node_id)]

    best_total = _INF
    meeting_node: str | None = None

    while heap_f and heap_b:
        if heap_f[0][0] + heap_b[0][0] >= best_total:
            break

        expand_forward = heap_f[0][0] <= heap_b[0][0]
        if expand_forward:
            dist_u, u = heapq.heappop(heap_f)
            if dist_u > dist_f.get(u, _INF):
                continue
            for v, weight in adjacency.get(u, []):
                nd = dist_u + weight
                _relax(dist_f, parent_f, heap_f, u, v, nd)
                total = dist_f.get(v, _INF) + dist_b.get(v, _INF)
                if total < best_total:
                    best_total = total
                    meeting_node = v
        else:
            dist_u, u = heapq.heappop(heap_b)
            if dist_u > dist_b.get(u, _INF):
                continue
            for v, weight in reverse_adjacency.get(u, []):
                nd = dist_u + weight
                _relax(dist_b, parent_b, heap_b, u, v, nd)
                total = dist_f.get(v, _INF) + dist_b.get(v, _INF)
                if total < best_total:
                    best_total = total
                    meeting_node = v

    if meeting_node is None or best_total == _INF:
        raise NoRouteError()

    forward_path = _path_to_origin(parent_f, start_node_id, meeting_node)
    if not forward_path:
        raise NoRouteError()

    suffix = _path_toward_end(parent_b, end_node_id, meeting_node)
    node_ids = forward_path + suffix

    return DijkstraResult(
        node_ids=node_ids,
        graph_distance_meters=best_total,
    )


def _relax(
    dist: dict[str, float],
    parent: dict[str, str | None],
    heap: list[tuple[float, str]],
    u: str,
    v: str,
    nd: float,
) -> None:
    cur = dist.get(v, _INF)
    if nd < cur:
        dist[v] = nd
        parent[v] = u
        heapq.heappush(heap, (nd, v))
    elif nd == cur and _prefer_parent(u, parent.get(v)):
        parent[v] = u


def _prefer_parent(candidate: str, existing: str | None) -> bool:
    if existing is None:
        return True
    return candidate < existing


def _path_to_origin(
    parent: dict[str, str | None],
    origin: str,
    target: str,
) -> list[str]:
    if target not in parent:
        return []
    rev: list[str] = []
    current: str | None = target
    while current is not None:
        rev.append(current)
        if current == origin:
            break
        current = parent.get(current)
    if not rev or rev[-1] != origin:
        return []
    rev.reverse()
    return rev


def _path_toward_end(
    parent: dict[str, str | None],
    end_node_id: str,
    meeting_node: str,
) -> list[str]:
    if meeting_node == end_node_id:
        return []
    suffix: list[str] = []
    current: str | None = parent.get(meeting_node)
    while current is not None:
        suffix.append(current)
        if current == end_node_id:
            break
        current = parent.get(current)
    if not suffix or suffix[-1] != end_node_id:
        return []
    return suffix
