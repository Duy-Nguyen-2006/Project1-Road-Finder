from __future__ import annotations

import math
from typing import Iterable

from app.infrastructure.graph_loader import GraphBBox, GraphNode
from app.utils.distance import haversine_meters

GRID_ROWS = 16
GRID_COLS = 16


class GridSpatialIndex:
    def __init__(self, nodes: dict[str, GraphNode], bbox: GraphBBox) -> None:
        self._bbox = bbox
        self._nodes = nodes
        self._lat_span = bbox.max_latitude - bbox.min_latitude or 1e-9
        self._lon_span = bbox.max_longitude - bbox.min_longitude or 1e-9
        self._buckets: dict[tuple[int, int], list[str]] = {}
        for node_id, node in nodes.items():
            cell = self._cell_for(node.latitude, node.longitude)
            self._buckets.setdefault(cell, []).append(node_id)

    def nearest_node_id(self, latitude: float, longitude: float) -> str:
        center = self._cell_for(latitude, longitude)
        best_id = ""
        best_dist = math.inf
        seen_cells: set[tuple[int, int]] = set()

        for ring in range(max(GRID_ROWS, GRID_COLS) + 1):
            for cell in self._cells_in_ring(center, ring):
                if cell in seen_cells:
                    continue
                seen_cells.add(cell)
                for node_id in self._buckets.get(cell, []):
                    node = self._nodes[node_id]
                    dist = haversine_meters(
                        latitude,
                        longitude,
                        node.latitude,
                        node.longitude,
                    )
                    if dist < best_dist or (
                        math.isclose(dist, best_dist) and node_id < best_id
                    ):
                        best_dist = dist
                        best_id = node_id

            if best_id and best_dist <= self._min_distance_to_unsearched(
                latitude, longitude, seen_cells
            ):
                return best_id

        if not best_id:
            for node_id, node in sorted(self._nodes.items()):
                dist = haversine_meters(
                    latitude, longitude, node.latitude, node.longitude
                )
                if dist < best_dist or (
                    math.isclose(dist, best_dist) and node_id < best_id
                ):
                    best_dist = dist
                    best_id = node_id
        return best_id

    def _cell_for(self, latitude: float, longitude: float) -> tuple[int, int]:
        row = self._row_index(latitude)
        col = self._col_index(longitude)
        return (row, col)

    def _row_index(self, latitude: float) -> int:
        ratio = (latitude - self._bbox.min_latitude) / self._lat_span
        ratio = min(max(ratio, 0.0), 1.0)
        return min(int(ratio * GRID_ROWS), GRID_ROWS - 1)

    def _col_index(self, longitude: float) -> int:
        ratio = (longitude - self._bbox.min_longitude) / self._lon_span
        ratio = min(max(ratio, 0.0), 1.0)
        return min(int(ratio * GRID_COLS), GRID_COLS - 1)

    def _cells_in_ring(
        self, center: tuple[int, int], ring: int
    ) -> Iterable[tuple[int, int]]:
        row0, col0 = center
        if ring == 0:
            yield center
            return
        for row in range(row0 - ring, row0 + ring + 1):
            for col in range(col0 - ring, col0 + ring + 1):
                if max(abs(row - row0), abs(col - col0)) != ring:
                    continue
                if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                    yield (row, col)

    def _min_distance_to_unsearched(
        self,
        latitude: float,
        longitude: float,
        seen_cells: set[tuple[int, int]],
    ) -> float:
        best = math.inf
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if (row, col) in seen_cells:
                    continue
                cell_lat_min, cell_lat_max, cell_lon_min, cell_lon_max = (
                    self._cell_bounds(row, col)
                )
                closest_lat = min(
                    max(latitude, cell_lat_min), cell_lat_max
                )
                closest_lon = min(
                    max(longitude, cell_lon_min), cell_lon_max
                )
                dist = haversine_meters(
                    latitude, longitude, closest_lat, closest_lon
                )
                best = min(best, dist)
        return best if math.isfinite(best) else 0.0

    def _cell_bounds(
        self, row: int, col: int
    ) -> tuple[float, float, float, float]:
        lat_step = self._lat_span / GRID_ROWS
        lon_step = self._lon_span / GRID_COLS
        lat_min = self._bbox.min_latitude + row * lat_step
        lat_max = lat_min + lat_step
        lon_min = self._bbox.min_longitude + col * lon_step
        lon_max = lon_min + lon_step
        return lat_min, lat_max, lon_min, lon_max
