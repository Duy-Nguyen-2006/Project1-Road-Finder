from pathlib import Path

import pytest

from app.application.cost_matrix import CostMatrix
from app.application.graph_runtime import build_graph_runtime
from app.domain.cost_model import RoutingOptions
from app.domain.tsp import Stop
from app.domain.vrp import (
    FleetPlan,
    _find_cheapest_insertion_in_tour,
    _inter_route_relocate,
    _try_relocate_order,
    solve_vrp,
)

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


def test_cheapest_insertion_into_nonempty_destination_tour(cost_matrix):
    dst_stops = [
        Stop(order_id="o3", kind="pickup", node_id="node-start"),
        Stop(order_id="o3", kind="dropoff", node_id="node-mid"),
    ]
    pickup = Stop(order_id="o2", kind="pickup", node_id="node-north")
    dropoff = Stop(order_id="o2", kind="dropoff", node_id="node-south")

    inserted = _find_cheapest_insertion_in_tour(
        dst_stops,
        pickup,
        dropoff,
        "node-north",
        cost_matrix,
    )

    assert inserted is not None
    order_ids = {stop.order_id for stop in inserted}
    assert order_ids == {"o2", "o3"}


def test_try_relocate_order_preserves_destination_orders(cost_matrix):
    src_stops = [
        Stop(order_id="o1", kind="pickup", node_id="node-mid"),
        Stop(order_id="o1", kind="dropoff", node_id="node-end"),
        Stop(order_id="o2", kind="pickup", node_id="node-north"),
        Stop(order_id="o2", kind="dropoff", node_id="node-south"),
    ]
    dst_stops = [
        Stop(order_id="o3", kind="pickup", node_id="node-start"),
        Stop(order_id="o3", kind="dropoff", node_id="node-mid"),
    ]
    shipper_nodes = {"s1": "node-start", "s2": "node-north"}

    result = _try_relocate_order(
        "s1",
        "s2",
        "o2",
        src_stops,
        pickup_idx=2,
        dropoff_idx=3,
        dst_stops=dst_stops,
        shipper_nodes=shipper_nodes,
        cost_matrix=cost_matrix,
    )

    assert result is not None
    new_src, new_dst, _ = result
    assert {stop.order_id for stop in new_src} == {"o1"}
    assert {stop.order_id for stop in new_dst} == {"o2", "o3"}


def test_inter_route_relocate_keeps_all_assigned_orders(cost_matrix):
    tours = {
        "s1": [
            Stop(order_id="o1", kind="pickup", node_id="node-mid"),
            Stop(order_id="o1", kind="dropoff", node_id="node-end"),
            Stop(order_id="o2", kind="pickup", node_id="node-north"),
            Stop(order_id="o2", kind="dropoff", node_id="node-south"),
        ],
        "s2": [
            Stop(order_id="o3", kind="pickup", node_id="node-start"),
            Stop(order_id="o3", kind="dropoff", node_id="node-mid"),
        ],
    }
    shipper_nodes = {"s1": "node-start", "s2": "node-north"}

    relocated = _inter_route_relocate(tours, shipper_nodes, cost_matrix)

    served = {
        stop.order_id
        for stops in relocated.values()
        for stop in stops
    }
    assert served == {"o1", "o2", "o3"}


def test_heuristic_vrp_serves_all_orders_with_multiple_shippers(cost_matrix):
    options = RoutingOptions(vrp_brute_force_max_orders=0, vrp_brute_force_max_shippers=0)
    result = solve_vrp(
        shipper_ids=["s1", "s2"],
        shipper_nodes={"s1": "node-start", "s2": "node-north"},
        orders=[
            ("o1", "node-mid", "node-end"),
            ("o2", "node-north", "node-south"),
            ("o3", "node-start", "node-mid"),
        ],
        cost_matrix=cost_matrix,
        options=options,
    )

    served = {
        stop.order_id
        for _, tour in result.tours
        for stop in tour.ordered_stops
    }
    assert served == {"o1", "o2", "o3"}
    assert result.unassigned_order_ids == []
