# Road Finder — VRP Delivery Routing

Web app giúp tối ưu giao vận đa-shipper trên bản đồ TP.HCM. User chọn nhiều
điểm **Pickup** / **Dropoff** cho mỗi đơn hàng và nhiều vị trí **Shipper**,
backend chạy **Bidirectional Dijkstra** trên local road graph (có hướng, có
`oneway` + `road_type`), từ đó gợi ý phân đội (assignment) / tối ưu tuyến
cho 1 shipper (TSP) / tối ưu đội nhiều shipper nhiều đơn (VRP). Frontend vẽ
polyline từng leg + danh sách stop theo shipper lên bản đồ Leaflet và hiển
thị tổng khoảng cách tự động định dạng `m` / `km`.

Project direction: local Ho Chi Minh City road graph JSON + directed
Bidirectional Dijkstra + 4 flows (route, assignment, tour, fleet). Tất cả
flow dùng chung `CostMatrix` + `RouteCache` + leg shape (`route_points` +
`distance_meters` + `kind`).

## Tính năng chính

- Hiển thị bản đồ bằng Leaflet + OpenStreetMap tiles.
- Khi app load: gọi `GET /graph/bounds` để lấy bbox + `max_snap_distance_meters`
  + `graph_version`; vẽ bbox đỏ lên map và fit view.
- Click trong bbox theo 3 mode:
  - **Order + Pickup** → click lấy điểm lấy hàng.
  - **Order + Dropoff** → click lấy điểm giao hàng (sau khi đã chọn pickup).
  - **Shipper** → click đặt vị trí shipper.
- Click ngoài bbox: không đặt marker, không thay đổi state, hiển thị
  `Error: Not in accepted area`.
- Bấm **Tối ưu đội**: gọi `POST /fleet` với toàn bộ shipper + đơn đã chọn +
  routing options (avoid_road_types / avoid_edge_ids).
- Backend snap mỗi điểm về node gần nhất trong local graph (max 200m, nếu
  vượt thì 422).
- Tính `CostMatrix` (Bidirectional Dijkstra many-to-many, cache theo
  `graph_version` + `options_hash` + cặp node).
- Branch theo flow:
  - `POST /route`: 1 điểm → 1 điểm, trả polyline + distance.
  - `POST /assignments`: 1 đơn + N shipper → ranking + recommended (tổng
    quãng đường 2 leg: shipper→pickup, pickup→dropoff).
  - `POST /tours`: 1 shipper + N đơn → 1 tour tối ưu (TSP: brute-force ≤8
    stops, nearest-neighbor + 2-opt cho lớn hơn).
  - `POST /fleet`: M shipper + N đơn → M tour + `unassigned_order_ids` (VRP:
    cheapest-insertion + intra 2-opt + inter relocate; brute-force ≤3 đơn
    với ≤2 shipper).
- Reconstruct `route_points` cho từng leg = `[clicked_start, ...graph_nodes,
  clicked_end]`, distance = snap + graph + snap.
- Frontend vẽ polyline màu theo shipper, auto-fit map theo tổng polylines,
  hiển thị `total_distance_meters` dạng m/km; `optimal=true` highlight khi
  brute-force chạy.
- Đổi điểm clear kết quả cũ; nút **Xóa tất cả** xoá toàn bộ.

## Tech stack

### Frontend (`frontend/`)

- React 18 + Vite
- React Leaflet (Leaflet 1.9.x) cho map + marker + polyline + rectangle
- TanStack Query cho `getGraphBounds` (cache vĩnh viễn) + `postFleet` mutation
- Fetch API (axios chỉ khai báo dep nhưng không import runtime)

### Backend (`backend/`)

- Python 3.10+ + FastAPI + Uvicorn
- Pydantic v2 cho request/response validation
- Pure Python stdlib cho algorithm: `heapq` (Bidirectional Dijkstra), `math`
  (Haversine), `itertools.permutations` + `itertools.product` cho brute-force

### Map data

- OpenStreetMap tiles (chỉ cho UI)
- **Local HCM road graph** ở `backend/app/data/road_graph.json` (committed,
  < 50MB, hỗ trợ `oneway` + `road_type` để áp cost multiplier). Generator ở
  `scripts/generate_hcm_graph.py` (osmnx + networkx + Geofabrik PBF, chạy
  offline).
- **Không** gọi runtime Overpass / OSRM. Test `test_no_external_runtime.py`
  chặn mọi HTTP ngoài ở runtime backend.

## Cấu trúc thư mục

```text
Project1-Road-Finder/
├── backend/
│   ├── app/
│   │   ├── main.py                              # FastAPI app + lifespan load graph
│   │   ├── application/                         # use case orchestration
│   │   │   ├── cost_matrix.py                   # many-to-many Dijkstra + cache
│   │   │   ├── graph_bounds.py                  # /graph/bounds payload
│   │   │   ├── graph_runtime.py                 # GraphRuntime + adjacency cache
│   │   │   ├── health.py                        # /health payload
│   │   │   ├── node_lookup.py                   # node id → coordinate
│   │   │   └── snap_service.py                  # bbox + 200m snap
│   │   ├── domain/                              # pure business rules
│   │   │   ├── assignment.py                    # rank_shippers_for_order
│   │   │   ├── cost_model.py                    # RoutingOptions + multipliers
│   │   │   ├── dijkstra.py                      # bidirectional_dijkstra
│   │   │   ├── graph.py                         # directed adjacency + reverse
│   │   │   ├── graph_types.py                   # GraphNode/Edge/Metadata
│   │   │   ├── protocols.py                     # DistanceProvider/NodeLookup
│   │   │   ├── route_reconstruction.py          # dedupe + distance formula
│   │   │   ├── tsp.py                           # optimize_tour (NN + 2-opt + brute)
│   │   │   ├── vrp.py                           # solve_vrp + cheapest_insertion
│   │   │   └── errors.py                        # AcceptedAreaError, NoRouteError
│   │   ├── http/route_errors.py                 # domain → HTTPException mapping
│   │   ├── infrastructure/
│   │   │   ├── graph_loader.py                  # load + validate JSON
│   │   │   ├── grid_index.py                    # spatial bucket
│   │   │   └── route_cache.py                   # LRU by version + opts + nodes
│   │   ├── models/                              # Pydantic DTOs
│   │   │   ├── point.py
│   │   │   └── route_models.py                  # route/assignment/tour/fleet DTOs
│   │   ├── routers/route_api.py                 # 6 endpoints (xem API contract)
│   │   ├── services/
│   │   │   ├── leg_builder.py                   # snap-aware leg builder
│   │   │   ├── route_computation.py             # /route pipeline
│   │   │   ├── shortest_path_service.py         # cache-aware Dijkstra wrapper
│   │   │   └── tour_response_builder.py         # /tours + /fleet + /assignments leg builder
│   │   ├── utils/distance.py                    # Haversine (km + meters)
│   │   └── data/road_graph.json                 # local HCM graph (committed)
│   ├── tests/
│   │   ├── unit/                                # loader, dijkstra, snapper, cache,
│   │   │                                        # reconstruct, runtime, cost_model,
│   │   │                                        # assignment, tsp, vrp, directed_graph
│   │   └── integration/                         # /health, /graph/bounds, /route,
│   │                                            # /assignments, /tours, /fleet,
│   │                                            # no_external_runtime
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/routeApi.js                      # getGraphBounds + postRoute + postAssignments + postTours + postFleet
│   │   ├── components/
│   │   │   ├── MapView.jsx                      # tile + bbox rectangle + shipper/order markers + tour polylines
│   │   │   ├── ModeSwitcher.jsx                 # Order (Pickup/Dropoff) ↔ Shipper
│   │   │   ├── OptionsPanel.jsx                 # avoid_road_types checkbox
│   │   │   ├── FleetResultPanel.jsx             # per-shipper tour summary + unassigned
│   │   │   └── PointList.jsx                    # order + shipper list với remove
│   │   ├── hooks/useVrpState.js                 # state: orders, shippers, fleetResult, status, avoidRoadTypes
│   │   ├── utils/
│   │   │   ├── format.js                        # formatDistance (m/km)
│   │   │   └── geo.js                           # isInsideBbox, bboxToLeaflet
│   │   ├── App.jsx                              # useQuery bounds + useMutation fleet
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── generate_hcm_graph.py                    # offline HCM graph generator scaffold
│   └── bin/harness-cli                          # Rust CLI (Harness v0 durable layer)
├── docs/                                        # product/architecture/context rules + harness
├── droid-wiki/                                  # generated wiki (out of git track)
├── plans/
├── Walkthrough.md                               # progress tracker (đã reconcile với VRP)
└── README.md                                    # file này
```

## Yêu cầu môi trường

- Python 3.10+
- Node.js 18+
- npm
- Internet chỉ cần cho OpenStreetMap tiles khi mở UI (backend không gọi
  internet sau khi graph đã load)

## Cài đặt & chạy

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chạy backend (mặc định load `backend/app/data/road_graph.json`):

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Override đường dẫn graph qua env:

```bash
ROAD_FINDER_GRAPH_PATH=/path/to/other.json uvicorn app.main:app --reload
```

Backend chạy tại `http://localhost:8000`. Startup sẽ fail nếu graph thiếu
hoặc malformed (`GraphValidationError`). Swagger UI: `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại `http://localhost:5173`. Nếu backend ở URL khác:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## API contract

Tất cả request/response dùng JSON. Error shape mặc định của FastAPI:
`{ "detail": "..." }`.

### `GET /health`

```json
{
  "status": "ok",
  "graph": { "loaded": true, "graph_version": "hcm-fixture-v2", "node_count": 6, "edge_count": 5 },
  "cache": { "route_cache_size": 0, "route_cache_limit": 1000 }
}
```

### `GET /graph/bounds`

```json
{
  "bbox": { "min_latitude": 10.70, "min_longitude": 106.60, "max_latitude": 10.90, "max_longitude": 106.90 },
  "max_snap_distance_meters": 200,
  "graph_version": "hcm-fixture-v2"
}
```

### `POST /route` — 1 điểm → 1 điểm

Request:

```json
{
  "start": { "latitude": 10.778109, "longitude": 106.714456 },
  "end":   { "latitude": 10.770016, "longitude": 106.720633 },
  "options": { "avoid_road_types": [], "avoid_edge_ids": [] }
}
```

Response 200:

```json
{
  "route_points": [
    { "latitude": 10.778109, "longitude": 106.714456 },
    { "latitude": 10.777968, "longitude": 106.714375 },
    { "latitude": 10.770016, "longitude": 106.720633 }
  ],
  "distance": 1234.5
}
```

### `POST /assignments` — 1 đơn + N shipper → ranking

Request:

```json
{
  "order": {
    "id": "o1",
    "pickup":  { "latitude": 10.778109, "longitude": 106.714456 },
    "dropoff": { "latitude": 10.770016, "longitude": 106.720633 }
  },
  "shippers": [
    { "id": "s1", "location": { "latitude": 10.779000, "longitude": 106.715000 } }
  ],
  "options": { "avoid_road_types": ["highway"], "avoid_edge_ids": [] }
}
```

Response 200: ranking các shipper với `total_distance_meters` = leg
`to_pickup` + leg `to_dropoff`, có `feasible`, `recommended_shipper_id`.

### `POST /tours` — 1 shipper + N đơn → 1 tour (TSP)

Request:

```json
{
  "shipper": { "id": "s1", "location": { "latitude": 10.779000, "longitude": 106.715000 } },
  "orders": [
    { "id": "o1", "pickup": { "latitude": 10.778109, "longitude": 106.714456 }, "dropoff": { "latitude": 10.770016, "longitude": 106.720633 } }
  ],
  "options": { "avoid_road_types": [], "avoid_edge_ids": [] }
}
```

Response 200: `ordered_stops` (mỗi stop có `order_id`, `kind`, `coordinate`),
`legs` (mỗi leg có `kind`, `distance_meters`, `route_points`), `total_distance_meters`,
`optimal` (true khi brute-force chạy, len(stops) ≤ 8).

### `POST /fleet` — M shipper + N đơn → M tour + unassigned (VRP)

Request:

```json
{
  "shippers": [
    { "id": "s1", "location": { "latitude": 10.779000, "longitude": 106.715000 } },
    { "id": "s2", "location": { "latitude": 10.780000, "longitude": 106.716000 } }
  ],
  "orders": [
    { "id": "o1", "pickup": { "latitude": 10.778109, "longitude": 106.714456 }, "dropoff": { "latitude": 10.770016, "longitude": 106.720633 } },
    { "id": "o2", "pickup": { "latitude": 10.781000, "longitude": 106.717000 }, "dropoff": { "latitude": 10.782000, "longitude": 106.718000 } }
  ],
  "options": { "avoid_road_types": ["highway"], "avoid_edge_ids": [] }
}
```

Response 200: `tours` (mỗi tour giống shape `/tours`), `unassigned_order_ids`
(đơn không thể gán do disconnects / inf cost), `total_distance_meters`,
`optimal` (true khi brute-force chạy, len(orders) ≤ 3 và len(shippers) ≤ 2).

### Error shape

| Condition | Status | detail |
| --- | ---: | --- |
| Invalid body / lat-lng out of range | 422 | FastAPI validation |
| Point ngoài bbox / nearest > 200m | 422 | `Error: Not in accepted area` |
| No graph path giữa snapped nodes | 404 | `No route found between selected points` |
| Graph missing/malformed | startup fail | n/a |

## Luồng hoạt động (VRP flow chính)

1. User mở frontend.
2. Frontend gọi `GET /graph/bounds` (TanStack Query, cache vĩnh viễn).
3. Frontend vẽ bbox đỏ, fit map tới bbox.
4. User chọn mode **Order**, click trong bbox → đặt pickup.
5. Mode tự chuyển sang **Dropoff**, user click → đặt dropoff → tạo order,
   mode reset về **Pickup** cho order tiếp theo.
6. User chọn mode **Shipper**, click → đặt vị trí shipper.
7. Click ngoài bbox: hiển thị `Error: Not in accepted area`, không thay đổi
   state.
8. User chọn avoid_road_types trong OptionsPanel (optional).
9. User bấm **Tối ưu đội** → frontend gọi `POST /fleet`.
10. Backend snap mỗi điểm về node local graph (≤ 200m).
11. Backend build `CostMatrix` cho tập node (shippers + pickups + dropoffs).
12. `solve_vrp` chạy cheapest-insertion + intra 2-opt + inter relocate
    (hoặc brute-force khi input nhỏ).
13. Backend reconstruct legs với `leg_builder` (snap + graph nodes + snap
    dedupe), trả `tours` + `unassigned_order_ids` + `total_distance_meters`
    + `optimal`.
14. Frontend vẽ polyline màu theo shipper, auto-fit map, hiển thị
    `total_distance_meters` dạng m/km + `FleetResultPanel` với từng tour +
    danh sách unassigned.

## Kiểm thử nhanh

Backend unit + integration (111 tests, deterministic):

```bash
cd backend
.venv/bin/python -m pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```

Smoke test API (sau khi chạy backend):

```bash
curl http://localhost:8000/health
curl http://localhost:8000/graph/bounds
curl -X POST http://localhost:8000/route \
  -H 'content-type: application/json' \
  -d '{"start":{"latitude":10.778109,"longitude":106.714456},"end":{"latitude":10.770016,"longitude":106.720633}}'
```

## Ghi chú

- HCM graph mặc định (`backend/app/data/road_graph.json`) hiện là
  `hcm-fixture-v2` (6 node / 5 cạnh, có `oneway` + `road_type`) cho
  unit/integration test deterministic. Để smoke test trên TP.HCM thật,
  chạy `scripts/generate_hcm_graph.py` (cần `osmnx` + `networkx` +
  Geofabrik `vietnam-latest.osm.pbf`) rồi commit file mới với
  `graph_version = hcm-v1`.
- Cost model áp dụng multiplier theo `road_type` (`highway` ×0.8,
  `residential` ×1.2, `trunk` ×0.85, …). `avoid_road_types` set cost
  = inf cho mọi cạnh thuộc type đó.
- Bidirectional Dijkstra chạy forward trên directed adjacency, backward
  trên reverse adjacency (đúng `oneway`).
- `RouteCache` LRU 1000, key = `(graph_version, options_hash, src_node,
  dst_node)`. `CostMatrix` reuse cache này, không tự chạy lại Dijkstra.
- OSRM smoothing chỉ là future enhancement (SPEC §11). Hiện tại dùng thẳng
  `route_points` từ local graph — polyline là chuỗi đoạn thẳng nối các
  node, không phải geometry đường cong.
- Drag marker, real-time re-route, traffic, turn-by-turn, accounts, saved
  routes, drag marker đều out of scope MVP.
