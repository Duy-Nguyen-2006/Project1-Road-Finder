# US-002 — POST /assignments

## Status

in_progress

## Lane

normal

## Product Contract

Cho phép caller (vd dashboard operations, internal script) gán 1 đơn hàng
cho shipper tốt nhất trong N shipper có sẵn. Backend rank shipper theo
tổng quãng đường 2 leg: `to_pickup` (shipper → pickup) + `to_dropoff`
(pickup → dropoff). Trả về ranking + `recommended_shipper_id` (rank 1
feasible). Tôn trọng `RoutingOptions`.

## Relevant Product Docs

- `docs/product/api.md` — `POST /assignments` contract
- `docs/product/routing.md` — assignment + CostMatrix
- `docs/product/overview.md` — sub-flow context

## Acceptance Criteria

- Request body: `{ order: OrderRequest, shippers: list<ShipperRequest>, options?: RoutingOptionsRequest }`.
- Response 200: `{ recommended_shipper_id: str | null, ranking: list<ShipperRouteResponse> }`.
- Mỗi `ranking[i]`:
  - `shipper_id`, `feasible: bool`, `total_distance_meters: float`,
    `legs: list<LegResponse>` (1 hoặc 2 leg tuỳ feasibility).
- `feasible = true` khi cả 2 leg (`to_pickup` + `to_dropoff`) đều finite.
- Ranking sort tăng dần theo `total_distance_meters` (chỉ tính feasible
  trước, inf cuối).
- `recommended_shipper_id` = shipper rank 1 feasible, hoặc `null` nếu
  không có shipper nào feasible.
- Snap fail (order hoặc shipper ngoài bbox / > 200m): HTTP 422 với
  detail `Error: Not in accepted area` (fail-fast ở shipper / order đầu
  tiên lỗi).
- Empty `shippers`: response ranking rỗng, `recommended_shipper_id = null`,
  status 200.
- `legs[].kind` = `"to_pickup"` hoặc `"to_dropoff"` — không hardcode nội
  dung khác.

## Design Notes

- **API**: `POST /assignments` (`backend/app/routers/route_api.py:91-149`).
- **Models**: `AssignmentRequest`, `AssignmentResponse`, `OrderRequest`,
  `ShipperRequest`, `ShipperRouteResponse`, `LegResponse`
  (`backend/app/models/route_models.py`).
- **Pipeline**:
  1. Build `CostMatrix(runtime, options)` pre-compute cho tập node:
     `[shipper_node_ids..., pickup_node_id, dropoff_node_id]`.
  2. `rank_shippers_for_order` (`backend/app/domain/assignment.py`):
     - Với mỗi shipper: cost `to_pickup` = `matrix.get(shipper_node,
       pickup_node)`, cost `to_dropoff` = `matrix.get(pickup_node,
       dropoff_node)`.
     - Tổng = sum. `feasible` = cả 2 leg finite.
     - Sort tăng dần, track rank 1.
  3. Build response legs qua `build_assignment_leg` (lookup graph nodes →
     reconstruct polyline + distance cho từng leg).
- **CostMatrix** reuse `RouteCache` (LRU 1000), không chạy Dijkstra lặp.
- Snap fail raise `AcceptedAreaError` → 422.

## Validation

`scripts/bin/harness-cli story update --id US-002 --unit 1 --integration 1 --e2e 0 --platform 0`

| Layer | Expected proof |
| --- | --- |
| Unit | `test_assignment_tour.py`, `test_cost_model.py`, `test_snapper.py` |
| Integration | `test_route_api.py::test_assignments_ranking_with_recommendation`, `test_assignments_422_outside_bbox`, `test_assignments_empty_shippers`, `test_assignments_infeasible_shipper` |
| E2E | (P15) FE dashboard gọi `/assignments` với 1 đơn + 3 shipper |
| Platform | n/a |
| Release | `pytest -q` (111/111 pass) |

## Harness Delta

- Cập nhật story packet với proof status khi verify.
- Thêm story verify command: `cd backend && .venv/bin/python -m pytest tests/unit/test_assignment_tour.py tests/integration/test_route_api.py -q -k assignment`

## Evidence

- `backend/tests/unit/test_assignment_tour.py` — rank + feasible + precedence
- `backend/tests/integration/test_route_api.py` — request/response + errors
- `docs/product/api.md` — request/response example
