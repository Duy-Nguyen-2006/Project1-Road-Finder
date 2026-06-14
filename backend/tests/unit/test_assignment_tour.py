import json
from pathlib import Path

import pytest

from app.application.cost_matrix import CostMatrix
from app.application.graph_runtime import build_graph_runtime
from app.domain.assignment import rank_shippers_for_order
from app.domain.tsp import Stop, optimize_tour

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


@pytest.fixture
def cost_matrix(runtime):
    cm = CostMatrix(runtime)
    # All nodes in fixture
    all_nodes = list(runtime.nodes.keys())
    cm.compute_for_nodes(all_nodes)
    return cm


def test_cost_matrix_self_distance_is_zero(cost_matrix):
    for node_id in ["node-start", "node-mid", "node-end"]:
        assert cost_matrix.get_distance(node_id, node_id) == pytest.approx(0.0)


def test_cost_matrix_symmetric_for_bidirectional_edges(cost_matrix):
    dist_forward = cost_matrix.get_distance("node-start", "node-mid")
    dist_reverse = cost_matrix.get_distance("node-mid", "node-start")
    assert dist_forward == pytest.approx(dist_reverse)


def test_cost_matrix_path_exists(cost_matrix):
    path = cost_matrix.get_path("node-start", "node-end")
    assert path is not None
    assert len(path) >= 2
    assert path[0] == "node-start"
    assert path[-1] == "node-end"


def test_assignment_ranks_shippers_by_distance(cost_matrix):
    # 2 shippers at different locations
    shipper_ids = ["s1", "s2"]
    shipper_nodes = {
        "s1": "node-start",
        "s2": "node-mid",
    }
    pickup_node = "node-north"
    dropoff_node = "node-end"

    result = rank_shippers_for_order(
        shipper_ids, shipper_nodes, pickup_node, dropoff_node, cost_matrix
    )

    assert result.recommended_shipper_id is not None
    assert len(result.ranking) == 2
    # All should be feasible
    assert all(r.feasible for r in result.ranking)
    # Should be sorted by distance
    assert result.ranking[0].total_distance_meters <= result.ranking[1].total_distance_meters


def test_assignment_recommends_closest_shipper(cost_matrix):
    shipper_ids = ["s1", "s2"]
    shipper_nodes = {
        "s1": "node-start",  # closer to pickup
        "s2": "node-end",    # farther
    }
    pickup_node = "node-mid"
    dropoff_node = "node-end"

    result = rank_shippers_for_order(
        shipper_ids, shipper_nodes, pickup_node, dropoff_node, cost_matrix
    )

    # s1 (node-start) is closer to node-mid than s2 (node-end)
    assert result.recommended_shipper_id == "s1"


def test_tour_optimal_for_two_orders(cost_matrix):
    stops = [
        Stop(order_id="o1", kind="pickup", node_id="node-start"),
        Stop(order_id="o1", kind="dropoff", node_id="node-mid"),
        Stop(order_id="o2", kind="pickup", node_id="node-north"),
        Stop(order_id="o2", kind="dropoff", node_id="node-end"),
    ]

    tour = optimize_tour("node-start", stops, cost_matrix)

    assert tour.total_distance_meters > 0
    assert len(tour.ordered_stops) == 4

    # Check precedence: pickup before dropoff for each order
    seen = {}
    for stop in tour.ordered_stops:
        if stop.order_id not in seen:
            seen[stop.order_id] = []
        seen[stop.order_id].append(stop.kind)

    for order_id, kinds in seen.items():
        pickup_idx = kinds.index("pickup")
        dropoff_idx = kinds.index("dropoff")
        assert pickup_idx < dropoff_idx


def test_tour_empty_stops(cost_matrix):
    tour = optimize_tour("node-start", [], cost_matrix)
    assert tour.total_distance_meters == pytest.approx(0.0)
    assert tour.optimal is True


def test_tour_single_order(cost_matrix):
    stops = [
        Stop(order_id="o1", kind="pickup", node_id="node-mid"),
        Stop(order_id="o1", kind="dropoff", node_id="node-end"),
    ]

    tour = optimize_tour("node-start", stops, cost_matrix)

    assert tour.total_distance_meters > 0
    assert len(tour.ordered_stops) == 2
    assert tour.ordered_stops[0].kind == "pickup"
    assert tour.ordered_stops[1].kind == "dropoff"
