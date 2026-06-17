# US-001 — POST /route

## Status

in_progress

## Lane

normal

## Product Contract

Cho phép caller (FE smoke test, internal integration, hoặc downstream API)
hỏi tuyến đường ngắn nhất giữa 2 điểm bất kỳ trong bbox đỏ TP.HCM.
Backend snap về node local graph, chạy Bidirectional Dijkstra trên đồ thị
có hướng (`oneway` + `road_type` cost multiplier), reconstruct polyline +
distance. Tôn trọng `RoutingOptions` (`avoid_road_types` / `avoid_edge_ids`)
của caller.

## Relevant Product Docs

- `docs/product/api.md` — `POST /route` contract
- `docs/product/routing.md` — Bidirectional Dijkstra, cost model, snap, reconstruct
- `docs/product/overview.md` — flow context
- `README.md` — quickstart

## Acceptance Criteria

- Request body: `{ start: Point, end: Point, options?: RoutingOptionsRequest }`.
- Response 200: `{ route_points: list<Point>, distance: float >= 0 }`.
- Snap fail (point ngoài bbox / nearest > 200m): HTTP 422 + detail
  `Error: Not in accepted area`.
- Disconnected: HTTP 404 + detail `No route found between selected points`.
- Invalid body (lat/lng out of range, missing field): HTTP 422 từ FastAPI
  validation.
- Cùng `(graph_version, options_hash, src_node_id, end_node_id)` qua
  RouteCache LRU 1000 — call thứ 2 trả cùng distance với cost cache hit.
- `options.avoid_road_types = ["highway"]` → cost của mọi cạnh `highway`
  = inf, Dijkstra không đi qua. Verify distance tăng hoặc trở thành
  `No route found` nếu đường thay thế không tồn tại.
- `start == end` (cùng lat/lng): trả polyline `[clicked_point]` +
  distance = 0 (snap về node rồi distance = 0).
- Reconstruct dedupe exact adjacent coordinates (tolerance 1e-9) — không
  có đoạn zero-length trong polyline.

## Design Notes

- **API**: `POST /route` (`backend/app/routers/route_api.py:75-89`).
- **Models**: `RouteRequest`, `RouteResponse`, `RoutingOptionsRequest`
  (`backend/app/models/route_models.py`).
- **Pipeline**:
  1. `_to_routing_options(body.options)` → `RoutingOptions`.
  2. `compute_shortest_path_response(runtime, start, end, options)`
     (`backend/app/services/route_computation.py`):
     - `find_cached_or_compute_graph_path` (`shortest_path_service.py`):
       snap start + snap end → cache lookup → nếu miss chạy
       `bidirectional_dijkstra(adjacency, start_node, end_node, reverse_adjacency)`
       → `RouteCache.put` → return `GraphPathResult`.
     - `reconstruct_route` (`domain/route_reconstruction.py`):
       `[clicked_start, ...graph_nodes, clicked_end]` + dedupe +
       `distance = start_snap + graph_distance + end_snap`.
  3. Wrap thành `RouteResponse(route_points, distance)`.
- **Adjacency cache** keyed theo `options_hash` để tránh rebuild khi
  options giống (`GraphRuntime.adjacency_for`).
- **Snap** raise `AcceptedAreaError` → `http_exception_for_domain_error`
  → 422 với detail `ACCEPTED_AREA_DETAIL`.
- **No-route** raise `NoRouteError` → 404 với detail `NO_ROUTE_DETAIL`.

## Validation

`scripts/bin/harness-cli story update --id US-001 --unit 1 --integration 1 --e2e 0 --platform 0`

| Layer | Expected proof |
| --- | --- |
| Unit | `test_route_reconstruction.py`, `test_dijkstra.py`, `test_snapper.py`, `test_cost_model.py`, `test_route_cache.py` |
| Integration | `test_route_api.py::test_route_happy_path`, `test_route_outside_bbox_returns_422`, `test_route_disconnected_returns_404`, `test_route_invalid_latitude_returns_422`, `test_route_avoids_road_types` |
| E2E | (P15) Open browser, click 2 điểm trong TP.HCM, gọi qua UI |
| Platform | n/a |
| Release | `pytest -q` (111/111 pass) |

## Harness Delta

- Cập nhật `docs/stories/epics/E01-vrp-delivery-routing/US-001-post-route.md`
  với proof status khi verify.
- Thêm story verify command: `cd backend && .venv/bin/python -m pytest tests/unit tests/integration -q`

## Evidence

- `backend/tests/integration/test_route_api.py` — happy + 422 + 404 + invalid
- `backend/tests/unit/test_route_reconstruction.py` — dedupe + distance formula
- `backend/tests/unit/test_dijkstra.py` — directed + tie-break + same start/end
- `backend/tests/unit/test_route_cache.py` — options isolation + reverse reuse rule
- `docs/product/api.md` — request/response example
