import pytest

from app.domain.cost_model import RoutingOptions, edge_cost


def test_edge_cost_default_multiplier():
    options = RoutingOptions()
    assert edge_cost(100.0, "default", options) == pytest.approx(100.0)


def test_edge_cost_highway_multiplier():
    options = RoutingOptions()
    assert edge_cost(100.0, "highway", options) == pytest.approx(80.0)


def test_edge_cost_residential_multiplier():
    options = RoutingOptions()
    assert edge_cost(100.0, "residential", options) == pytest.approx(120.0)


def test_edge_cost_tertiary_multiplier():
    options = RoutingOptions()
    assert edge_cost(100.0, "tertiary", options) == pytest.approx(110.0)


def test_edge_cost_primary_multiplier():
    options = RoutingOptions()
    assert edge_cost(100.0, "primary", options) == pytest.approx(90.0)


def test_edge_cost_unknown_road_type_uses_default():
    options = RoutingOptions()
    assert edge_cost(100.0, "unknown_type", options) == pytest.approx(100.0)


def test_edge_cost_avoid_road_type_returns_inf():
    options = RoutingOptions(avoid_road_types=("residential",))
    assert edge_cost(100.0, "residential", options) == float("inf")


def test_edge_cost_avoid_does_not_affect_other_types():
    options = RoutingOptions(avoid_road_types=("residential",))
    assert edge_cost(100.0, "highway", options) == pytest.approx(80.0)


def test_edge_cost_multiple_avoided_types():
    options = RoutingOptions(avoid_road_types=("residential", "tertiary"))
    assert edge_cost(100.0, "residential", options) == float("inf")
    assert edge_cost(100.0, "tertiary", options) == float("inf")
    assert edge_cost(100.0, "highway", options) == pytest.approx(80.0)


def test_routing_options_defaults():
    options = RoutingOptions()
    assert options.avoid_road_types == ()
    assert options.avoid_edge_ids == ()
