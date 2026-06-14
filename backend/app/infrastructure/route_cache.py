from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

DEFAULT_ROUTE_CACHE_LIMIT = 1000


@dataclass(frozen=True)
class CachedGraphPath:
    node_ids: list[str]
    graph_distance_meters: float


def make_cache_key(
    graph_version: str,
    options_hash: str,
    start_node_id: str,
    end_node_id: str,
) -> str:
    return f"{graph_version}|{options_hash}|{start_node_id}|{end_node_id}"


def cache_lookup_key(
    graph_version: str,
    options_hash: str,
    start_node_id: str,
    end_node_id: str,
) -> str:
    return make_cache_key(graph_version, options_hash, start_node_id, end_node_id)


@dataclass
class RouteCache:
    limit: int = DEFAULT_ROUTE_CACHE_LIMIT

    def __post_init__(self) -> None:
        self._entries: OrderedDict[str, CachedGraphPath] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self._entries)

    def get(
        self,
        graph_version: str,
        options_hash: str,
        start_node_id: str,
        end_node_id: str,
    ) -> CachedGraphPath | None:
        direct_key = make_cache_key(
            graph_version, options_hash, start_node_id, end_node_id
        )
        if direct_key in self._entries:
            self._entries.move_to_end(direct_key)
            return self._entries[direct_key]

        return None

    def put(
        self,
        graph_version: str,
        options_hash: str,
        start_node_id: str,
        end_node_id: str,
        path: CachedGraphPath,
    ) -> None:
        key = make_cache_key(
            graph_version, options_hash, start_node_id, end_node_id
        )
        if key in self._entries:
            self._entries.move_to_end(key)
        self._entries[key] = path
        while len(self._entries) > self.limit:
            self._entries.popitem(last=False)
