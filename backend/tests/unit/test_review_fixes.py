import math
from pathlib import Path

import pytest

from app.application.cost_matrix import CostMatrix
from app.application.graph_runtime import build_graph_runtime
from app.domain.assignment import AssignmentSnapContext, rank_shippers_for_order
from app.domain.tsp import Stop, optimize_tour
from app.infrastructure.route_cache import RouteCache

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def test_cost_matrix_computes_on_demand(runtime):
    cm = CostMatrix(runtime)
    dist = cm.get_distance("node-start", "node-end")
    assert dist is not None
    assert dist > 0


def test_assignment_ranking_uses_snap_context(runtime):
    cm = CostMatrix(runtime)
    all_nodes = list(runtime.nodes.keys())
    cm.compute_for_nodes(all_nodes)

    snap_context = AssignmentSnapContext(
        shipper_snap_distances={"s1": 1000.0, "s2": 0.0},
        pickup_snap_distance=10.0,
        dropoff_snap_distance=5.0,
    )
    result = rank_shippers_for_order(
        shipper_ids=["s1", "s2"],
        shipper_nodes={"s1": "node-start", "s2": "node-start"},
        pickup_node="node-north",
        dropoff_node="node-end",
        cost_matrix=cm,
        snap_context=snap_context,
    )

    assert result.ranking[0].shipper_id == "s2"
    assert result.recommended_shipper_id == "s2"


def test_optimize_tour_marks_infeasible_without_json_inf(runtime):
    cm = CostMatrix(runtime)
    cm.compute_for_nodes(list(runtime.nodes.keys()))
    stops = [
        Stop(order_id="o1", kind="pickup", node_id="node-start"),
        Stop(order_id="o1", kind="dropoff", node_id="node-end"),
    ]

    tour = optimize_tour("node-start", stops, cm, options=None)

    assert tour.feasible is True
    assert math.isfinite(tour.total_distance_meters)


def test_route_cache_is_thread_safe_under_concurrent_access():
    from app.infrastructure.route_cache import CachedGraphPath

    cache = RouteCache(limit=10)
    path = CachedGraphPath(node_ids=["a", "b"], graph_distance_meters=1.0)

    import threading

    def writer():
        for i in range(50):
            cache.put("v", "o", f"s{i}", f"d{i}", path)

    def reader():
        for i in range(50):
            cache.get("v", "o", f"s{i}", f"d{i}")

    threads = [
        threading.Thread(target=writer if i % 2 == 0 else reader)
        for i in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert cache.size <= cache.limit