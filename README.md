# Road Finder

Road Finder là web app chọn đúng 2 điểm **Start** và **End** trong vùng bbox đỏ của TP.HCM, gửi lên backend, backend chạy **Bidirectional Dijkstra** trên local road graph rồi trả về polyline tuyến đường ngắn nhất. Frontend vẽ polyline đó lên bản đồ Leaflet và hiển thị khoảng cách tự động định dạng `m` / `km`.

Project direction: local Ho Chi Minh City road graph JSON + Bidirectional Dijkstra + Start/End only. Waypoint/TSP/OSRM runtime đã được loại bỏ khỏi MVP.

## Tính năng chính

- Hiển thị bản đồ bằng Leaflet và OpenStreetMap tiles.
- Khi app load: gọi `GET /graph-bounds` để lấy bbox + `max_snap_distance_meters` + `graph_version`; vẽ bbox đỏ lên map và fit view.
- Chọn đúng 1 điểm Start và 1 điểm End bằng cách chuyển chế độ (Start / End) rồi click lên map.
- Click ngoài bbox: không đặt marker, không thay đổi state hiện tại, hiển thị `Error: Not in accepted area`.
- Bấm **Find Shortest Path**: gọi `POST /shortest-path`.
- Backend snap Start/End về node gần nhất trong local graph (max 200m, nếu vượt thì 422).
- Backend chạy Bidirectional Dijkstra trên local graph, reconstruct `route_points` + `distance` + `start_node_id` + `end_node_id`.
- Frontend vẽ polyline từ `route_points` và auto-fit map theo polyline; hiển thị distance tự động định dạng `m` / `km`.
- Đổi Start/End clear route cũ; nút **Clear** xoá toàn bộ.

## Tech stack

### Frontend (`frontend/`)

- React 18 + Vite
- React Leaflet (Leaflet 1.9.x) cho map + marker + polyline + rectangle
- TanStack Query cho `getGraphBounds` (cache vĩnh viễn) + `findShortestPath` mutation
- Fetch API (không dùng axios runtime)

### Backend (`backend/`)

- Python 3.10+ + FastAPI + Uvicorn
- Pydantic cho request/response validation
- Pure Python stdlib cho algorithm: heapq (Bidirectional Dijkstra) + Haversine

### Map data

- OpenStreetMap tiles (chỉ cho UI)
- **Local HCM road graph** ở `backend/app/data/road_graph.json` (committed, < 50MB). Generator ở `scripts/generate_hcm_graph.py` (osmnx + networkx + Geofabrik PBF, chạy offline).
- **Không** gọi runtime Overpass hay OSRM trong MVP.

## Cấu trúc thư mục

```text
Project1-Road-Finder/
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI app + lifespan load graph
│   │   ├── application/                  # health, graph_bounds, graph_runtime
│   │   ├── domain/                       # dijkstra, graph, snapper, route_reconstruction, errors
│   │   ├── http/                         # route_errors (domain → HTTP mapping)
│   │   ├── infrastructure/               # graph_loader, grid_index, route_cache
│   │   ├── models/                       # Pydantic: Point, route_models
│   │   ├── routers/route_api.py          # /health, /graph-bounds, /shortest-path, /optimize-route
│   │   ├── services/                     # shortest_path_service, route_computation
│   │   ├── utils/distance.py             # Haversine (km + meters)
│   │   └── data/road_graph.json          # local HCM graph (committed)
│   ├── tests/
│   │   ├── unit/                         # loader, dijkstra, snapper, cache, reconstruct, runtime, payload, errors
│   │   └── integration/                  # /health + cache sequence, /graph-bounds, /shortest-path, /optimize-route, no external HTTP
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/routeApi.js               # findShortestPath + getGraphBounds + checkHealth
│   │   ├── components/
│   │   │   ├── MapView.jsx               # tile + bbox rectangle + start/end markers + polyline
│   │   │   ├── RouteControls.jsx         # Start/End toggle + Find Shortest Path + Clear
│   │   │   └── PointList.jsx             # Start/End list
│   │   ├── hooks/useRoutePoints.js       # state: start, end, route, status, errorMessage
│   │   ├── utils/                        # format.js (formatDistance), geo.js (isInsideBbox, bboxToLeaflet)
│   │   ├── App.jsx                       # useQuery bounds + useMutation shortest-path
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── generate_hcm_graph.py             # offline HCM graph generator (osmnx + networkx)
│   └── sync-github-wiki.sh
├── docs/                                 # product/architecture/context rules
├── plans/
├── Walkthrough.md                        # 17-phase progress tracker
├── SPEC.md                               # source of truth
└── README.md                             # file này
```

## Yêu cầu môi trường

- Python 3.10+
- Node.js 18+
- npm
- Internet chỉ cần cho OpenStreetMap tiles khi mở UI (backend không gọi internet sau khi graph đã load)

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

Backend chạy tại `http://localhost:8000`. Startup sẽ fail nếu graph thiếu hoặc malformed.

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

### `GET /health`

```json
{
  "status": "ok",
  "graph": { "loaded": true, "graph_version": "hcm-v1", "node_count": 1000, "edge_count": 3000 },
  "cache": { "route_cache_size": 0, "route_cache_limit": 1000 }
}
```

### `GET /graph-bounds`

```json
{
  "bbox": { "min_latitude": 10.70, "min_longitude": 106.60, "max_latitude": 10.90, "max_longitude": 106.90 },
  "max_snap_distance_meters": 200,
  "graph_version": "hcm-v1"
}
```

### `POST /shortest-path`

Request:

```json
{
  "start": { "latitude": 10.778109, "longitude": 106.714456 },
  "end":   { "latitude": 10.770016, "longitude": 106.720633 }
}
```

Response:

```json
{
  "route_points": [
    { "latitude": 10.778109, "longitude": 106.714456 },
    { "latitude": 10.777968, "longitude": 106.714375 },
    { "latitude": 10.770016, "longitude": 106.720633 }
  ],
  "distance": 1234.5,
  "start_node_id": "node-123",
  "end_node_id": "node-456"
}
```

### `POST /optimize-route` (legacy wrapper, chỉ để tương thích caller cũ)

- Chấp nhận đúng 2 `points`. Trả về cùng shape như `/shortest-path` (field `route_points`, không phải `ordered_points`).
- Reject 0/1/3+ points với HTTP 422 + `"optimize-route requires exactly two points"`.
- Frontend **không** dùng endpoint này trong flow MVP.

### Error shape (FastAPI default `{ "detail": "..." }`)

| Condition | Status | detail |
| --- | ---: | --- |
| Invalid body / lat-lng out of range | 422 | FastAPI validation |
| Point ngoài bbox / nearest > 200m | 422 | `Error: Not in accepted area` |
| No graph path giữa snapped nodes | 404 | `No route found between selected points` |
| Graph missing/malformed | startup fail | n/a |

## Luồng hoạt động

1. User mở frontend.
2. Frontend gọi `GET /graph-bounds` (TanStack Query, cache vĩnh viễn).
3. Frontend vẽ bbox đỏ, fit map tới bbox.
4. User chọn chế độ Start, click trong bbox → đặt marker Start.
5. User chọn chế độ End, click trong bbox → đặt marker End.
6. Click ngoài bbox: hiển thị `Error: Not in accepted area`, không thay đổi state.
7. User bấm **Find Shortest Path** → frontend gọi `POST /shortest-path`.
8. Backend snap Start/End về node local graph gần nhất (≤ 200m).
9. Backend check cache → nếu miss chạy Bidirectional Dijkstra trên local graph.
10. Backend reconstruct `route_points` (clicked Start + graph nodes + clicked End) + `distance` (snap segments + graph path).
11. Frontend vẽ polyline từ `route_points`, auto-fit map, hiển thị `distance` dạng m/km.

## Kiểm thử nhanh

Backend unit + integration:

```bash
cd backend
.venv/bin/python -m pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```

Smoke test API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/graph-bounds
```

## Ghi chú

- HCM graph file mặc định (`backend/app/data/road_graph.json`) hiện là **fixture 4 node / 2 edge** (`graph_version = hcm-fixture-v1`) để unit/integration test deterministic. Để smoke test trên TP.HCM thật, chạy `scripts/generate_hcm_graph.py` (cần `osmnx` + `networkx` + Geofabrik `vietnam-latest.osm.pbf`) rồi commit file mới với `graph_version = hcm-v1`.
- OSRM smoothing chỉ là future enhancement (SPEC §11). MVP hiện tại dùng thẳng `route_points` từ local graph — polyline là chuỗi đoạn thẳng nối các node, không phải geometry đường cong.
- Drag marker, waypoint, one-way, turn-by-turn, accounts, saved routes, traffic đều out of scope MVP.
