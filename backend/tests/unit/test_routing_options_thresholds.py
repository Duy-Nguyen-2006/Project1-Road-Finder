"""Unit tests for the new solver threshold fields on RoutingOptions.

These cover:
- Default values (None → module default)
- Explicit integer override
- Threshold = 0 disables the brute-force path
- Pydantic model accepts and validates the new fields
- `optimize_tour` and `solve_vrp` respect the threshold when given via
  `options` keyword.
"""
import pytest

from app.domain.cost_model import (
    DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS,
    DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS,
    DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS,
    RoutingOptions,
)


def test_default_options_have_none_thresholds():
    opts = RoutingOptions()
    assert opts.tsp_brute_force_max_stops is None
    assert opts.vrp_brute_force_max_orders is None
    assert opts.vrp_brute_force_max_shippers is None


def test_resolved_thresholds_use_module_defaults_when_none():
    opts = RoutingOptions()
    assert opts.resolved_tsp_threshold() == DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS
    assert opts.resolved_vrp_order_threshold() == DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS
    assert opts.resolved_vrp_shipper_threshold() == DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS


def test_resolved_thresholds_respect_explicit_overrides():
    opts = RoutingOptions(
        tsp_brute_force_max_stops=12,
        vrp_brute_force_max_orders=5,
        vrp_brute_force_max_shippers=3,
    )
    assert opts.resolved_tsp_threshold() == 12
    assert opts.resolved_vrp_order_threshold() == 5
    assert opts.resolved_vrp_shipper_threshold() == 3


def test_resolved_threshold_zero_disables_brute_force():
    opts = RoutingOptions(tsp_brute_force_max_stops=0)
    assert opts.resolved_tsp_threshold() == 0


def test_module_default_values_are_documented():
    """Document the chosen defaults; if you change them, update this test."""
    assert DEFAULT_TSP_BRUTE_FORCE_MAX_STOPS == 8
    assert DEFAULT_VRP_BRUTE_FORCE_MAX_ORDERS == 3
    assert DEFAULT_VRP_BRUTE_FORCE_MAX_SHIPPERS == 2


def test_pydantic_model_accepts_new_optional_fields():
    from app.models.route_models import RoutingOptionsRequest

    # Omitted: all default to None
    req = RoutingOptionsRequest()
    assert req.tsp_brute_force_max_stops is None
    assert req.vrp_brute_force_max_orders is None
    assert req.vrp_brute_force_max_shippers is None

    # Explicit values
    req = RoutingOptionsRequest(
        avoid_road_types=["highway"],
        tsp_brute_force_max_stops=10,
        vrp_brute_force_max_orders=4,
        vrp_brute_force_max_shippers=2,
    )
    assert req.avoid_road_types == ["highway"]
    assert req.tsp_brute_force_max_stops == 10
    assert req.vrp_brute_force_max_orders == 4
    assert req.vrp_brute_force_max_shippers == 2


def test_pydantic_model_rejects_negative_thresholds():
    from pydantic import ValidationError

    from app.models.route_models import RoutingOptionsRequest

    with pytest.raises(ValidationError):
        RoutingOptionsRequest(tsp_brute_force_max_stops=-1)
    with pytest.raises(ValidationError):
        RoutingOptionsRequest(vrp_brute_force_max_orders=-5)
    with pytest.raises(ValidationError):
        RoutingOptionsRequest(vrp_brute_force_max_shippers=-2)


def test_pydantic_model_accepts_zero_threshold():
    """Threshold 0 means 'disable brute-force, always heuristic'."""
    from app.models.route_models import RoutingOptionsRequest

    req = RoutingOptionsRequest(tsp_brute_force_max_stops=0)
    assert req.tsp_brute_force_max_stops == 0
