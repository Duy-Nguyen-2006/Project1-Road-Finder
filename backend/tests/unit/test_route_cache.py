import json
from pathlib import Path

import pytest

from app.application.graph_runtime import build_graph_runtime
from app.domain.dijkstra import bidirectional_dijkstra
from app.infrastructure.route_cache import (
    CachedGraphPath,
    RouteCache,
    cache_lookup_key,
    make_cache_key,
)
from app.services.shortest_path_service import find_cached_or_compute_graph_path

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


def test_make_cache_key_uses_version_and_node_ids_only():
    assert make_cache_key("v1", "a", "b") == "v1|a|b"
    assert make_cache_key("v1", "a", "b") == make_cache_key("v1", "a", "b")


def test_first_put_increases_size():
    cache = RouteCache(limit=1000)
    cache.put(
        "v1",
        "node-start",
        "node-end",
        CachedGraphPath(node_ids=["node-start", "node-end"], graph_distance_meters=1.0),
    )
    assert cache.size == 1


def test_get_moves_entry_to_mru_for_lru_eviction():
    cache = RouteCache(limit=2)
    cache.put("v", "a", "b", CachedGraphPath(["a", "b"], 1.0))
    cache.put("v", "c", "d", CachedGraphPath(["c", "d"], 2.0))
    assert cache.get("v", "a", "b") is not None
    cache.put("v", "e", "f", CachedGraphPath(["e", "f"], 3.0))
    assert cache.get("v", "c", "d") is None
    assert cache.get("v", "a", "b") is not None
    assert cache.size == 2


def test_lru_evicts_oldest_when_exceeding_limit():
    cache = RouteCache(limit=1000)
    for i in range(1001):
        cache.put(
            "v",
            f"n{i}",
            f"m{i}",
            CachedGraphPath(node_ids=[f"n{i}", f"m{i}"], graph_distance_meters=float(i)),
        )
    assert cache.size == 1000
    assert cache.get("v", "n0", "m0") is None
    assert cache.get("v", "n1000", "m1000") is not None


def test_reverse_lookup_reuses_forward_entry_with_reversed_nodes():
    cache = RouteCache()
    cache.put(
        "hcm-fixture-v1",
        "node-start",
        "node-end",
        CachedGraphPath(
            node_ids=["node-start", "node-mid", "node-end"],
            graph_distance_meters=300.5,
        ),
    )
    hit = cache.get("hcm-fixture-v1", "node-end", "node-start")
    assert hit is not None
    assert hit.node_ids == ["node-end", "node-mid", "node-start"]
    assert hit.graph_distance_meters == pytest.approx(300.5)
    assert cache.size == 1


def test_different_graph_version_is_distinct_key():
    cache = RouteCache()
    cache.put("v1", "a", "b", CachedGraphPath(["a", "b"], 1.0))
    assert cache.get("v2", "a", "b") is None
    assert cache.size == 1


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def test_service_same_snapped_pair_does_not_duplicate_cache_entries(runtime):
    start_a = (10.7785, 106.7149)
    start_b = (10.7786, 106.7150)
    end = (10.7808, 106.7172)
    first = find_cached_or_compute_graph_path(runtime, start_a, end)
    size_after_first = runtime.route_cache.size
    second = find_cached_or_compute_graph_path(runtime, start_b, end)
    assert second.from_cache is True
    assert runtime.route_cache.size == size_after_first
    assert first.graph_path.node_ids == second.graph_path.node_ids
    assert first.graph_path.graph_distance_meters == pytest.approx(
        second.graph_path.graph_distance_meters
    )


def test_service_reverse_reuses_cache_without_growing(runtime):
    forward = find_cached_or_compute_graph_path(
        runtime, (10.7785, 106.7149), (10.7808, 106.7172)
    )
    assert forward.from_cache is False
    size_one = runtime.route_cache.size
    reverse = find_cached_or_compute_graph_path(
        runtime, (10.7808, 106.7172), (10.7785, 106.7149)
    )
    assert reverse.from_cache is True
    assert runtime.route_cache.size == size_one
    assert reverse.graph_path.node_ids == list(reversed(forward.graph_path.node_ids))
    assert reverse.graph_path.graph_distance_meters == pytest.approx(
        forward.graph_path.graph_distance_meters
    )


def test_cache_lookup_key_matches_storage_key():
    assert cache_lookup_key("v", "a", "b") == make_cache_key("v", "a", "b")


def _write_versioned_graph(tmp_path: Path, version: str) -> Path:
    path = tmp_path / "graph.json"
    payload = {
        "metadata": {
            "graph_version": version,
            "bbox": {
                "min_latitude": 10.0,
                "min_longitude": 106.0,
                "max_latitude": 11.0,
                "max_longitude": 107.0,
            },
            "max_snap_distance_meters": 500.0,
        },
        "nodes": {
            "a": {"latitude": 10.5, "longitude": 106.5},
            "b": {"latitude": 10.51, "longitude": 106.51},
        },
        "edges": [{"from": "a", "to": "b", "distance": 10.0}],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_version_change_does_not_reuse_old_cache_entry(tmp_path):
    path_v1 = _write_versioned_graph(tmp_path, "cache-v1")
    rt1 = build_graph_runtime(path_v1)
    find_cached_or_compute_graph_path(rt1, (10.5, 106.5), (10.51, 106.51))
    assert rt1.route_cache.size == 1

    path_v2 = _write_versioned_graph(tmp_path, "cache-v2")
    rt2 = build_graph_runtime(path_v2)
    assert rt2.route_cache.size == 0
    result = find_cached_or_compute_graph_path(rt2, (10.5, 106.5), (10.51, 106.51))
    assert result.from_cache is False
    dijkstra = bidirectional_dijkstra(rt2.adjacency, "a", "b")
    assert result.graph_path.node_ids == dijkstra.node_ids
