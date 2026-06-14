from __future__ import annotations

from typing import Protocol


class DistanceProvider(Protocol):
    def get_distance(self, src_node: str, dst_node: str) -> float | None: ...

    def get_path(self, src_node: str, dst_node: str) -> list[str] | None: ...


class NodeCoordinateLookup(Protocol):
    def node_coordinate(self, node_id: str) -> tuple[float, float]: ...
