# Product Overview

Road Finder — VRP Delivery Routing là web app giúp tối ưu giao vận
đa-shipper trên bản đồ TP.HCM. User chọn nhiều **đơn hàng** (mỗi đơn có
pickup + dropoff) và nhiều **shipper** trên bản đồ, backend gợi ý phân
đội + tối ưu tuyến đường ngắn nhất theo ràng buộc pickup trước dropoff.

## Vision

Giúp dispatcher giao vận trong TP.HCM trực quan hoá và tối ưu phân công
shipper — đơn trong vài giây, không cần chạy solver ngoài.

## Primary Flow (fleet)

1. User mở web app.
2. App load `GET /graph/bounds`, vẽ bbox đỏ TP.HCM.
3. User chọn mode **Order**, click map lần 1 → pickup, click lần 2 → dropoff
   → tạo xong 1 order. Lặp lại cho mỗi đơn.
4. User chọn mode **Shipper**, click map → đặt vị trí shipper. Lặp lại
   cho mỗi shipper.
5. (Optional) User bật/tắt `avoid_road_types` trong OptionsPanel.
6. User bấm **Tối ưu đội** → gọi `POST /fleet`.
7. Backend trả `tours` (mỗi shipper 1 tour gồm `ordered_stops` + `legs` +
   `total_distance_meters`) + `unassigned_order_ids` + flag `optimal`.
8. Frontend vẽ polyline màu theo shipper, auto-fit map, hiển thị tổng
   khoảng cách + từng tour trong `FleetResultPanel`.

## Sub-Flows

- **Route** (`POST /route`): 1 điểm → 1 điểm. Dùng cho smoke test và
  tích hợp downstream.
- **Assignment** (`POST /assignments`): 1 đơn + N shipper → ranking +
  recommended. Dùng khi đã biết đơn cần gán và muốn xếp hạng shipper
  theo tổng quãng đường 2 leg.
- **Tour** (`POST /tours`): 1 shipper + N đơn → 1 tour tối ưu (TSP).
  Dùng khi đã biết shipper phụ trách và muốn sắp thứ tự đơn.

Cả 4 flow dùng chung `CostMatrix` (Bidirectional Dijkstra many-to-many
cached theo `graph_version` + `options_hash`) + `leg_builder` (snap +
graph + snap với dedupe).

## Out of Scope (MVP)

- Drag marker
- Real-time re-route khi shipper di chuyển
- Turn-by-turn navigation
- Live traffic
- User accounts / saved routes
- Mobile-native behavior
- OSRM geometry smoothing (SPEC §11 future)

## Stack

- **Backend**: FastAPI (Python 3.10+), Uvicorn, Pydantic v2, pure stdlib
  cho algorithm (`heapq` + `math` + `itertools`).
- **Frontend**: React 18 + Vite + React Leaflet + TanStack Query + fetch.
- **Data**: Local HCM road graph JSON (committed, < 50MB, hỗ trợ
  `oneway` + `road_type`).
- **Algorithm**: Bidirectional Dijkstra (directed), CostMatrix (cached),
  Assignment (rank), TSP (brute-force + nearest-neighbor + 2-opt),
  VRP (cheapest-insertion + intra 2-opt + inter relocate, brute-force cho
  instance nhỏ).

## Related Docs

- `routing.md` — Algorithm, cost model, graph details
- `api.md` — HTTP contracts cho 6 endpoint
- `frontend-flow.md` — UI state + component tree + tương tác
- `../../Walkthrough.md` — phase tracker
- `../../README.md` — quickstart + tổng quan
