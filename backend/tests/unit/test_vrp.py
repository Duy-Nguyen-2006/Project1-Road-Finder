from pathlib import Path

import pytest

from app.application.cost_matrix import CostMatrix
from app.application.graph_runtime import build_graph_runtime
from app.domain.vrp import FleetPlan, solve_vrp

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


@pytest.fixture
def cost_matrix(runtime):
    cm = CostMatrix(runtime)
    cm.compute_for_nodes(list(runtime.nodes.keys()))
    return cm


def test_vrp_single_shipper_single_order(cost_matrix):
    result = solve_vrp(
        shipper_ids=["s1"],
        shipper_nodes={"s1": "node-start"},
        orders=[("o1", "node-mid", "node-end")],
        cost_matrix=cost_matrix,
    )

    assert len(result.tours) == 1
    assert result.tours[0][0] == "s1"
    assert result.tours[0][1].total_distance_meters > 0
    assert len(result.tours[0][1].ordered_stops) == 2
    assert result.unassigned_order_ids == []


def test_vrp_precedence_respected(cost_matrix):
    result = solve_vrp(
        shipper_ids=["s1"],
        shipper_nodes={"s1": "node-start"},
        orders=[
            ("o1", "node-mid", "node-end"),
            ("o2", "node-north", "node-south"),
        ],
        cost_matrix=cost_matrix,
    )

    # Check precedence in each tour
    for sid, tour in result.tours:
        seen = {}
        for stop in tour.ordered_stops:
            if stop.order_id not in seen:
                seen[stop.order_id] = []
            seen[stop.order_id].append(stop.kind)

        for order_id, kinds in seen.items():
            pickup_idx = kinds.index("pickup")
            dropoff_idx = kinds.index("dropoff")
            assert pickup_idx < dropoff_idx


def test_vrp_two_shippers_two_orders(cost_matrix):
    result = solve_vrp(
        shipper_ids=["s1", "s2"],
        shipper_nodes={"s1": "node-start", "s2": "node-north"},
        orders=[
            ("o1", "node-mid", "node-end"),
            ("o2", "node-start", "node-north"),
        ],
        cost_matrix=cost_matrix,
    )

    assert len(result.tours) == 2
    assert result.total_distance_meters > 0
    # Both orders should be assigned
    all_order_ids = set()
    for sid, tour in result.tours:
        for stop in tour.ordered_stops:
            all_order_ids.add(stop.order_id)
    assert "o1" in all_order_ids
    assert "o2" in all_order_ids


def test_vrp_empty_orders(cost_matrix):
    result = solve_vrp(
        shipper_ids=["s1"],
        shipper_nodes={"s1": "node-start"},
        orders=[],
        cost_matrix=cost_matrix,
    )

    assert result.total_distance_meters == pytest.approx(0.0)
    assert result.optimal is True


def test_vrp_small_instance_brute_force(cost_matrix):
    """Small instance should use brute-force and be optimal."""
    result = solve_vrp(
        shipper_ids=["s1", "s2"],
        shipper_nodes={"s1": "node-start", "s2": "node-north"},
        orders=[
            ("o1", "node-mid", "node-end"),
        ],
        cost_matrix=cost_matrix,
        brute_force_threshold=4,
    )

    # Should be optimal since we used brute-force
    assert result.optimal is True
    assert result.total_distance_meters > 0
