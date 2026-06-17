# US-003 — POST /tours

## Status

in_progress

## Lane

normal

## Product Contract

Cho phép caller tối ưu thứ tự thăm pickup/dropoff cho 1 shipper với N
đơn hàng (bài toán TSP với ràng buộc precedence: pickup trước dropoff).
Backend snap mọi điểm, build `CostMatrix`, chạy `optimize_tour` (brute-force
≤ 8 stops cho kết quả optimal, nearest-neighbor + 2-opt lớn hơn). Trả
`ordered_stops`, `legs` (snap-aware polyline cho từng leg), `total_distance_meters`
+ flag `optimal`.

## Relevant Product Docs

- `docs/product/api.md` — `POST /tours` contract
- `docs/product/routing.md` — `optimize_tour` + brute-force vs heuristic
- `docs/product/overview.md` — sub-flow context

## Acceptance Criteria

- Request body: `{ shipper: ShipperRequest, orders: list<OrderRequest>, options?: RoutingOptionsRequest }`.
- Response 200: `{ shipper_id, ordered_stops: list<StopResponse>, legs: list<LegResponse>, total_distance_meters: float, optimal: bool }`.
- `ordered_stops`: thứ tự tối ưu, mỗi stop có `{ order_id, kind: "pickup"|"dropoff", coordinate }`.
- Ràng buộc precedence: trong `ordered_stops`, pickup của mỗi đơn phải
  xuất hiện trước dropoff của đơn đó. Verify unit test.
- `legs`: mỗi leg = `shipper → ordered_stops[0]` rồi `ordered_stops[i] →
  ordered_stops[i+1]`. `kind` = `f"{order_id}_{kind}"` (vd `"o1_pickup"`).
- `legs[].route_points` = `[clicked_start, ...graph_nodes, clicked_end]`
  với dedupe, `distance_meters` = snap + graph + snap.
- `total_distance_meters` = tổng các `legs[].distance_meters` (sum).
- `optimal = true` khi `len(ordered_stops) <= 8` (brute-force chạy).
  `optimal = false` khi dùng NN + 2-opt.
- Empty `orders`: response `ordered_stops=[]`, `legs=[]`,
  `total_distance_meters=0.0`, `optimal=true`.
- Snap fail: HTTP 422 với `Error: Not in accepted area`.
- 1 stop (vd đơn pickup ≡ shipper, không có dropoff khác): brute-force
  vẫn cho kết quả optimal.

## Design Notes

- **API**: `POST /tours` (`backend/app/routers/route_api.py:151-209`).
- **Models**: `TourRequest`, `TourResponse`, `OrderRequest`,
  `ShipperRequest`, `StopResponse`, `LegResponse`
  (`backend/app/models/route_models.py`).
- **Pipeline**:
  1. `snap_point` cho shipper + mỗi `(order.pickup, order.dropoff)`.
     Build `stops: list[Stop]`, `stop_coordinates`, `stop_snap_distances`.
  2. `CostMatrix.compute_for_nodes(all_nodes)` (shipper_node +
     pickup_nodes + dropoff_nodes).
  3. `optimize_tour(shipper_node, stops, cost_matrix)`
     (`backend/app/domain/tsp.py`):
     - ≤ 8 stops: brute-force permutation + `_check_precedence`
       (pickup trước dropoff) → trả `optimal=True`.
     - > 8 stops: nearest-neighbor (respect precedence) + 2-opt
       (giữ precedence) → trả `optimal=False`.
  4. `build_tour_legs` (`services/tour_response_builder.py`): với mỗi
     stop, build leg từ `current_node` → `stop.node_id` qua
     `leg_route_points_and_distance` (reconstruct polyline + distance).
- **CostMatrix** reuse `RouteCache`.
- Snap fail raise `AcceptedAreaError` → 422.

## Validation

`scripts/bin/harness-cli story update --id US-003 --unit 1 --integration 1 --e2e 0 --platform 0`

| Layer | Expected proof |
| --- | --- |
| Unit | `test_assignment_tour.py` (test tour part), `test_cost_model.py`, `test_snapper.py`, `test_route_reconstruction.py` |
| Integration | `test_route_api.py::test_tours_optimal_brute_force`, `test_tours_heuristic_large_input`, `test_tours_422_outside_bbox`, `test_tours_empty_orders`, `test_tours_precedence_constraint` |
| E2E | (P15) FE gọi `/tours` với 1 shipper + 4 đơn (1 đơn có pickup ≡ shipper) |
| Platform | n/a |
| Release | `pytest -q` (111/111 pass) |

## Harness Delta

- Cập nhật story packet với proof status khi verify.
- Story verify command: `cd backend && .venv/bin/python -m pytest tests/unit/test_assignment_tour.py tests/integration/test_route_api.py -q -k tour`

## Evidence

- `backend/tests/unit/test_assignment_tour.py` — TSP brute-force + NN + 2-opt + precedence
- `backend/tests/integration/test_route_api.py` — request/response + errors
- `docs/product/api.md` — request/response example
