# US-004 — POST /fleet

## Status

in_progress

## Lane

normal

## Product Contract

Cho phép caller tối ưu giao vận đội xe: M shipper + N đơn, backend
phân đơn cho shipper + sắp thứ tự thăm pickup/dropoff cho mỗi shipper
(bài toán VRP với ràng buộc precedence). Backend snap mọi điểm, build
`CostMatrix`, chạy `solve_vrp` (brute-force ≤ 3 đơn + ≤ 2 shipper cho
optimal, cheapest-insertion + intra 2-opt + inter relocate lớn hơn).
Trả `tours: list<FleetTourResponse>`, `unassigned_order_ids`,
`total_distance_meters` + flag `optimal`.

## Relevant Product Docs

- `docs/product/api.md` — `POST /fleet` contract
- `docs/product/routing.md` — `solve_vrp` + cheapest-insertion + local search
- `docs/product/overview.md` — primary flow
- `README.md` — primary flow

## Acceptance Criteria

- Request body: `{ shippers: list<ShipperRequest>, orders: list<OrderRequest>, options?: RoutingOptionsRequest }`.
- Response 200: `{ tours: list<FleetTourResponse>, unassigned_order_ids: list[str], total_distance_meters: float, optimal: bool }`.
- Mỗi `tours[i]` giống shape `TourResponse` (xem US-003): `shipper_id`,
  `ordered_stops`, `legs`, `total_distance_meters`, `optimal` riêng cho
  tour đó.
- `total_distance_meters` = tổng `tours[i].total_distance_meters` (chỉ
  tính tour có stops; shipper không có đơn vẫn có tour rỗng với
  `total_distance_meters=0.0`).
- `optimal = true` khi `len(orders) <= 3` AND `len(shippers) <= 2`
  (brute-force chạy). Mỗi `tours[i].optimal` riêng = true nếu tour
  brute-force (≤ 8 stops).
- `unassigned_order_ids`: đơn không gán được (disconnected, inf cost ở
  cả shipper, hoặc vi phạm precedence ở mọi assignment).
- Empty `orders`: response `tours=[]` (hoặc mỗi shipper 1 tour rỗng —
  check implementation), `unassigned_order_ids=[]`, `total=0.0`,
  `optimal=true`.
- Snap fail: HTTP 422 với `Error: Not in accepted area`.
- Ràng buộc precedence từng tour: pickup trước dropoff trong
  `ordered_stops` (giống US-003).
- 1 shipper + 1 đơn (1 stop): vẫn cho kết quả optimal.

## Design Notes

- **API**: `POST /fleet` (`backend/app/routers/route_api.py:211-274`).
- **Models**: `FleetRequest`, `FleetResponse`, `FleetTourResponse`
  (`backend/app/models/route_models.py`).
- **Pipeline**:
  1. `snap_point` cho từng shipper + mỗi `(order.pickup, order.dropoff)`.
     Build `shipper_nodes`, `shipper_snaps`, `orders_data`, `stop_coordinates`,
     `stop_snap_distances`.
  2. `CostMatrix.compute_for_nodes(all_nodes)`.
  3. `solve_vrp(shipper_ids, shipper_nodes, orders, cost_matrix)`
     (`backend/app/domain/vrp.py`):
     - ≤ 3 đơn + ≤ 2 shipper: brute-force `product(shipper_ids,
       repeat=len(orders))` assignment, mỗi assignment con shipper dùng
       `optimize_tour` brute-force → trả `optimal=True` cho cả plan.
     - Lớn hơn: `_cheapest_insertion` (cho từng đơn tìm shipper + vị
       trí insert tăng cost ít nhất) → `_intra_route_2opt` (từng tour)
       → `_inter_route_relocate` (move order giữa các shipper nếu tổng
       cost giảm) → trả `optimal=False`.
  4. Build response tours qua `build_tour_legs` (giống US-003).
- **CostMatrix** reuse `RouteCache`.
- **Disconnected** stop: `dist=inf` trong matrix → trong `_inter_route_relocate`
  vẫn tính được (giữ lại), nhưng tour cuối cùng nếu dist inf → đẩy stop
  vào `unassigned_from_inf`.
- **Precedence** enforced qua `_check_precedence` trong TSP và
  `_insert_pickup_dropoff` trong VRP (chỉ insert dropoff ở vị trí ≥
  pickup pos).

## Validation

`scripts/bin/harness-cli story update --id US-004 --unit 1 --integration 1 --e2e 0 --platform 0`

| Layer | Expected proof |
| --- | --- |
| Unit | `test_vrp.py`, `test_assignment_tour.py` (TSP), `test_cost_model.py`, `test_snapper.py`, `test_route_cache.py` |
| Integration | `test_route_api.py::test_fleet_optimal_brute_force`, `test_fleet_heuristic_with_inter_relocate`, `test_fleet_unassigned_orders`, `test_fleet_422_outside_bbox`, `test_fleet_empty_orders` |
| E2E | (P15) FE gọi `/fleet` với 2 shipper + 3 đơn trong TP.HCM thật, verify UI polyline + total |
| Platform | n/a |
| Release | `pytest -q` (111/111 pass) |

## Harness Delta

- Cập nhật story packet với proof status khi verify.
- Story verify command: `cd backend && .venv/bin/python -m pytest tests/unit/test_vrp.py tests/integration/test_route_api.py -q -k fleet`
- Cập nhật `docs/HARNESS_BACKLOG.md` nếu có friction (vd brute-force
  thresholds cần expose qua config).

## Evidence

- `backend/tests/unit/test_vrp.py` — cheapest-insertion + intra 2-opt + inter relocate + brute-force + unassigned
- `backend/tests/unit/test_assignment_tour.py` — TSP cho từng shipper
- `backend/tests/integration/test_route_api.py` — request/response + errors
- `docs/product/api.md` — request/response example
- `README.md` — primary flow
- (P15) E2E UI screenshot với 2 shipper + 3 đơn TP.HCM thật
