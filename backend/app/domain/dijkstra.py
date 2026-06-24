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

    state = _BidirectionalState(start_node_id, end_node_id)

    while state.heap_f and state.heap_b:
        if state.heap_f[0][0] + state.heap_b[0][0] >= state.best_total:
            break

        expand_forward = state.heap_f[0][0] <= state.heap_b[0][0]
        if expand_forward:
            _expand_side(
                state.heap_f,
                state.dist_f,
                state.parent_f,
                adjacency,
                state,
            )
        else:
            _expand_side(
                state.heap_b,
                state.dist_b,
                state.parent_b,
                reverse_adjacency,
                state,
            )

    if state.meeting_node is None or state.best_total == _INF:
        raise NoRouteError()

    forward_path = _path_to_origin(state.parent_f, start_node_id, state.meeting_node)
    if not forward_path:
        raise NoRouteError()

    suffix = _path_toward_end(state.parent_b, end_node_id, state.meeting_node)
    node_ids = forward_path + suffix

    return DijkstraResult(
        node_ids=node_ids,
        graph_distance_meters=state.best_total,
    )


@dataclass
class _BidirectionalState:
    dist_f: dict[str, float]
    dist_b: dict[str, float]
    parent_f: dict[str, str | None]
    parent_b: dict[str, str | None]
    heap_f: list[tuple[float, str]]
    heap_b: list[tuple[float, str]]
    best_total: float
    meeting_node: str | None

    def __init__(self, start: str, end: str) -> None:
        self.dist_f = {start: 0.0}
        self.dist_b = {end: 0.0}
        self.parent_f = {start: None}
        self.parent_b = {end: None}
        self.heap_f = [(0.0, start)]
        self.heap_b = [(0.0, end)]
        self.best_total = _INF
        self.meeting_node = None


def _expand_side(
    heap: list[tuple[float, str]],
    dist: dict[str, float],
    parent: dict[str, str | None],
    adjacency: Adjacency,
    state: _BidirectionalState,
) -> None:
    dist_u, u = heapq.heappop(heap)
    if dist_u > dist.get(u, _INF):
        return
    for v, weight in adjacency.get(u, []):
        nd = dist_u + weight
        _relax(dist, parent, heap, u, v, nd)
        total = state.dist_f.get(v, _INF) + state.dist_b.get(v, _INF)
        if total < state.best_total:
            state.best_total = total
            state.meeting_node = v


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
