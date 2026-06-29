import pytest

VALID_START = {"latitude": 10.7785, "longitude": 106.7149}
VALID_END = {"latitude": 10.7808, "longitude": 106.7172}


def test_graph_bounds_returns_metadata(client):
    response = client.get("/graph/bounds")
    assert response.status_code == 200
    body = response.json()
    assert body["graph_version"] == "hcm-fixture-v2"
    assert body["max_snap_distance_meters"] == 200
    bbox = body["bbox"]
    assert bbox["min_latitude"] == pytest.approx(10.7)
    assert bbox["min_longitude"] == pytest.approx(106.6)
    assert bbox["max_latitude"] == pytest.approx(10.9)
    assert bbox["max_longitude"] == pytest.approx(106.9)


def test_route_same_coordinates_allows_zero_distance(client):
    point = {"latitude": 10.778109, "longitude": 106.714456}
    response = client.post("/route", json={"start": point, "end": point})
    assert response.status_code == 200
    body = response.json()
    assert body["distance"] == pytest.approx(0.0)
    assert len(body["route_points"]) >= 1


def test_route_invalid_latitude_returns_422(client):
    response = client.post(
        "/route",
        json={
            "start": {"latitude": 91.0, "longitude": 106.71},
            "end": VALID_END,
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_route_outside_bbox_returns_exact_detail(client):
    response = client.post(
        "/route",
        json={
            "start": {"latitude": 10.69, "longitude": 106.75},
            "end": VALID_END,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Error: Not in accepted area"


def test_route_disconnected_returns_404(client):
    response = client.post(
        "/route",
        json={
            "start": {"latitude": 10.7785, "longitude": 106.7149},
            "end": {"latitude": 10.75, "longitude": 106.65},
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No route found between selected points"


def test_route_is_deterministic(client):
    payload = {"start": VALID_START, "end": VALID_END}
    first = client.post("/route", json=payload).json()
    second = client.post("/route", json=payload).json()
    assert first["route_points"] == second["route_points"]
    assert first["distance"] == pytest.approx(second["distance"])


def test_route_endpoint_happy_path(client):
    response = client.post(
        "/route",
        json={"start": VALID_START, "end": VALID_END},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["distance"] > 0
    assert len(body["route_points"]) >= 2
    assert body["route_points"][0]["latitude"] == pytest.approx(
        VALID_START["latitude"]
    )
    assert body["route_points"][-1]["latitude"] == pytest.approx(
        VALID_END["latitude"]
    )


def test_route_endpoint_with_options(client):
    response = client.post(
        "/route",
        json={
            "start": VALID_START,
            "end": VALID_END,
            "options": {"avoid_road_types": [], "avoid_edge_ids": []},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["distance"] > 0


def test_route_endpoint_avoid_residential(client):
    """Avoiding residential should change the route (if alternate path exists)."""
    # First get default route
    default = client.post(
        "/route",
        json={"start": VALID_START, "end": VALID_END},
    ).json()

    # Then get route avoiding residential
    avoided = client.post(
        "/route",
        json={
            "start": VALID_START,
            "end": VALID_END,
            "options": {"avoid_road_types": ["residential"]},
        },
    )

    # If there's an alternate path, distance should differ
    # If no alternate path, should get 404
    if avoided.status_code == 200:
        avoided_body = avoided.json()
        assert avoided_body["distance"] > 0
        assert avoided_body["distance"] != pytest.approx(default["distance"])
    else:
        assert avoided.status_code == 404


def test_graph_bounds_new_endpoint(client):
    response = client.get("/graph/bounds")
    assert response.status_code == 200
    body = response.json()
    assert body["graph_version"] == "hcm-fixture-v2"


def test_assignments_happy_path(client):
    response = client.post(
        "/assignments",
        json={
            "order": {
                "id": "o1",
                "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
            },
            "shippers": [
                {"id": "s1", "location": {"latitude": 10.778109, "longitude": 106.714456}},
                {"id": "s2", "location": {"latitude": 10.785, "longitude": 106.710}},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_shipper_id"] is not None
    assert len(body["ranking"]) == 2
    # All shippers should be feasible for this connected graph
    assert all(r["feasible"] for r in body["ranking"])


def test_assignments_with_avoid(client):
    response = client.post(
        "/assignments",
        json={
            "order": {
                "id": "o1",
                "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
            },
            "shippers": [
                {"id": "s1", "location": {"latitude": 10.778109, "longitude": 106.714456}},
            ],
            "options": {"avoid_road_types": []},
        },
    )
    assert response.status_code == 200


def test_tours_happy_path(client):
    response = client.post(
        "/tours",
        json={
            "shipper": {
                "id": "s1",
                "location": {"latitude": 10.778109, "longitude": 106.714456},
            },
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["shipper_id"] == "s1"
    assert body["total_distance_meters"] > 0
    assert len(body["ordered_stops"]) == 2
    # Pickup should come before dropoff
    assert body["ordered_stops"][0]["kind"] == "pickup"
    assert body["ordered_stops"][1]["kind"] == "dropoff"


def test_tours_two_orders(client):
    response = client.post(
        "/tours",
        json={
            "shipper": {
                "id": "s1",
                "location": {"latitude": 10.778109, "longitude": 106.714456},
            },
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
                {
                    "id": "o2",
                    "pickup": {"latitude": 10.785, "longitude": 106.710},
                    "dropoff": {"latitude": 10.775, "longitude": 106.720},
                },
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["ordered_stops"]) == 4
    assert body["total_distance_meters"] > 0


def test_fleet_happy_path(client):
    response = client.post(
        "/fleet",
        json={
            "shippers": [
                {"id": "s1", "location": {"latitude": 10.778109, "longitude": 106.714456}},
                {"id": "s2", "location": {"latitude": 10.785, "longitude": 106.710}},
            ],
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
                {
                    "id": "o2",
                    "pickup": {"latitude": 10.785, "longitude": 106.710},
                    "dropoff": {"latitude": 10.7792, "longitude": 106.7155},
                },
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["tours"]) == 2
    assert body["total_distance_meters"] > 0
    assert body["unassigned_order_ids"] == []


def test_fleet_single_shipper(client):
    response = client.post(
        "/fleet",
        json={
            "shippers": [
                {"id": "s1", "location": {"latitude": 10.778109, "longitude": 106.714456}},
            ],
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["tours"]) == 1
    assert body["tours"][0]["shipper_id"] == "s1"


def test_fleet_threshold_zero_disables_brute_force(client):
    """With vrp_brute_force_max_orders=0, the brute-force path is skipped
    even on a small instance, so 'optimal' must be False."""
    response = client.post(
        "/fleet",
        json={
            "shippers": [
                {"id": "s1", "location": {"latitude": 10.778109, "longitude": 106.714456}},
                {"id": "s2", "location": {"latitude": 10.785, "longitude": 106.710}},
            ],
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
            ],
            "options": {
                "avoid_road_types": [],
                "avoid_edge_ids": [],
                "vrp_brute_force_max_orders": 0,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    # 1 order with 2 shippers would normally trigger brute-force (optimal=true),
    # but with threshold=0 the heuristic path is used.
    assert body["optimal"] is False


def test_tours_threshold_zero_disables_brute_force(client):
    """With tsp_brute_force_max_stops=0, the brute-force path is skipped
    even on a small instance, so 'optimal' must be False."""
    response = client.post(
        "/tours",
        json={
            "shipper": {
                "id": "s1",
                "location": {"latitude": 10.778109, "longitude": 106.714456},
            },
            "orders": [
                {
                    "id": "o1",
                    "pickup": {"latitude": 10.7792, "longitude": 106.7155},
                    "dropoff": {"latitude": 10.7805, "longitude": 106.7168},
                },
                {
                    "id": "o2",
                    "pickup": {"latitude": 10.785, "longitude": 106.710},
                    "dropoff": {"latitude": 10.775, "longitude": 106.720},
                },
            ],
            "options": {
                "avoid_road_types": [],
                "avoid_edge_ids": [],
                "tsp_brute_force_max_stops": 0,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    # 4 stops is under the default threshold (8), so brute-force would run
    # and return optimal=true; with the override to 0 it must be False.
    assert body["optimal"] is False
