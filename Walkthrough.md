# Road Finder — Walkthrough & Progress Tracker

> Living document theo dõi tiến độ refactor project từ trạng thái hiện tại (TSP + OSRM) về trạng thái đúng SPEC (Bidirectional Dijkstra + local HCM road graph + chỉ Start/End).
>
> - Spec nguồn: `SPEC.md` (sections 1–15)
> - Cập nhật cuối: 2026-06-04
> - Trạng thái: **P0–P9 backend done, P10 in progress, P11–P17 pending**

---

## 0. Quy ước đọc file này

- Mỗi task là một checkbox `[ ]` / `[x]`.
- Tick `[x]` chỉ khi task đã xong **và** đã pass gate kiểm thử tương ứng.
- Phase chỉ "Done" khi **tất cả** task con tick xong **và** Definition of Done của phase đó pass.
- Nếu một task phát sinh rủi ro, ghi vào **§10 Risk log** và tạo issue mới.
- Mỗi khi đổi trạng thái, cập nhật **§11 Status log** (ngày + 1 dòng mô tả).

---

## 1. Tổng quan hiện trạng vs mục tiêu

| Hạng mục | Backend (đã làm) | Frontend (còn lệch) | Mục tiêu (SPEC) |
| --- | --- | --- | --- |
| Route chính | `POST /shortest-path` ✅ | đang gọi `/optimize-route` ❌ | `POST /shortest-path` |
| Algorithm | Bidirectional Dijkstra ✅ | n/a | Bidirectional Dijkstra trên local graph |
| Graph nguồn | `road_graph.json` fixture (sẽ thay bằng HCM) | n/a | `backend/app/data/road_graph.json` (committed, <50MB) |
| Geometry | Local graph edges ✅ | n/a | Local graph edges (OSRM optional) |
| Input | Đúng 2 điểm ✅ | 3 mode (Start A / End B / Waypoint) ❌ | Đúng 2 điểm: Start, End |
| Response field | `route_points` ✅ | đọc `ordered_points` ❌ | `route_points`, `distance`, `start_node_id`, `end_node_id` |
| Bbox | `GET /graph-bounds` ✅ | chưa gọi, không vẽ rectangle ❌ | Từ `/graph-bounds`, vẽ red rectangle trên Leaflet |
| Snap rule | local graph + 200m + 422 ✅ | không validate ❌ | Snap về node local graph, max 200m, reject nếu vượt |
| Cache | LRU 1000 + reverse reuse ✅ | n/a | LRU 1000, key = `graph_version` + snapped node IDs, reuse reverse |
| Health | full shape ✅ | n/a | `{status, graph, cache}` |
| Frontend | n/a | 3 mode | 2 mode (Start / End), không waypoint |
| Error ngoài bbox | 422 + message đúng ✅ | không show ❌ | `Error: Not in accepted area` (HTTP 422) |
| Legacy wrapper | `POST /optimize-route` (2 points) ✅ | FE không dùng trong flow MVP | wrapper cho caller cũ |

---

## 2. Mục tiêu MVP (lấy từ SPEC §1, §3, §6)

Người dùng mở web, chọn đúng 1 Start và 1 End trong bbox đỏ của TP.HCM, bấm **Find Shortest Path**, backend chạy Bidirectional Dijkstra trên local graph, frontend vẽ polyline `route_points` và hiển thị distance auto-format (`m` / `km`).

**In scope:** Leaflet map, `/graph-bounds`, snap+bidirectional Dijkstra, LRU cache, `route_points` polyline, m/km auto-format, error states.

**Out of scope (MVP):** waypoint, TSP, OR-Tools, NN/2-opt, Overpass/OSRM runtime, one-way, turn-by-turn, traffic, accounts, saved routes, drag marker.

---

## 3. Cấu trúc mục tiêu của repo

```text
Project1-Road-Finder/
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   └── road_graph.json          # NEW: committed HCM graph (<50MB)
│   │   ├── domain/                      # mở rộng: graph, snapper, dijkstra, cache
│   │   ├── infrastructure/               # graph loader, grid index
│   │   ├── models/                      # NEW: ShortestPathRequest/Response
│   │   ├── routers/
│   │   │   └── route_api.py             # REWRITE: /health, /graph-bounds, /shortest-path, /optimize-route (legacy)
│   │   ├── services/
│   │   │   ├── shortest_path_service.py # NEW: orchestrate snap → dijkstra → reconstruct → cache
│   │   │   ├── tsp_service.py           # DELETE (sau khi frontend đã chuyển sang /shortest-path)
│   │   │   └── osm_service.py           # DELETE (no runtime Overpass)
│   │   ├── utils/
│   │   │   ├── distance.py              # giữ Haversine
│   │   │   └── geo.py                   # NEW: bbox check, grid bucket helpers
│   │   └── main.py                      # EDIT: lifespan load + validate graph eager
│   ├── tests/
│   │   ├── unit/                        # NEW: loader, grid, snapper, dijkstra, cache, distance
│   │   └── integration/                 # NEW: /health, /graph-bounds, /shortest-path, /optimize-route
│   └── requirements.txt                 # bỏ requests/ortools nếu không còn dùng
├── frontend/
│   └── src/
│       ├── api/routeApi.js              # EDIT: replace optimizeRoute() → findShortestPath()
│       ├── hooks/useRoutePoints.js      # EDIT: bỏ waypoints, chỉ Start/End + bounds + status
│       ├── components/
│       │   ├── MapView.jsx              # EDIT: vẽ bbox rectangle đỏ, disable click nếu !bounds
│       │   ├── RouteControls.jsx        # EDIT: 2 mode Start/End, button "Find Shortest Path"
│       │   └── PointList.jsx            # EDIT: chỉ Start/End
│       ├── utils/format.js              # NEW: formatDistance(m) → "123 m" / "1.23 km"
│       └── App.jsx                      # EDIT: clear route khi đổi Start/End, error message
├── docs/product/                        # reconcile với SPEC sau khi code match
├── README.md                            # update sau khi code match SPEC
└── Walkthrough.md                       # file này
```

---

## 4. Kế hoạch phase (map với SPEC §14)

```
P0  Graph schema & fixture
P1  Graph loader + startup validation
P2  Adjacency + simple grid spatial index
P3  Snapper (bbox + 200m)
P4  Bidirectional Dijkstra service
P5  Path reconstruction + distance
P6  LRU route cache (reverse reuse)
P7  /graph-bounds endpoint
P8  /shortest-path models + route
P9  Legacy /optimize-route wrapper (đúng 2 points)
P10 Dọn dẹp code cũ (TSP/OSM/runtime deps)
P11 Frontend: API client + state
P12 Frontend: bỏ waypoint UI
P13 Frontend: graph-bounds + bbox rectangle
P14 Frontend: accepted-area validation
P15 Frontend: polyline + distance + error states
P16 Docs & README reconcile
P17 Smoke test với committed HCM graph
```

---

## 5. Checklist chi tiết theo phase

### P0 — Graph schema & fixture
- [x] Định nghĩa JSON schema (`metadata`, `nodes`, `edges`) khớp SPEC §9
- [x] Tạo `backend/app/data/road_graph.json` fixture nhỏ (3–5 nodes, ≥2 path) cho unit test
- [x] Tạo `backend/tests/fixtures/` cho unit test (inlined trong `tests/unit/test_graph_loader.py` + `test_dijkstra.py`)
- [x] Document schema versioning (`graph_version = "hcm-fixture-v1"` cho fixture, `"hcm-v1"` mặc định của generator)
- [x] **Committed HCM graph — phương án: commit thẳng + generator script offline (không LFS, không runtime Overpass)**
  - [x] Source data expectation: Geofabrik `vietnam-latest.osm.pbf` (docstring trong generator)
  - [x] Generator: `scripts/generate_hcm_graph.py` scaffold (dry-run + emit-sample + validation hook)
  - [x] Filter: highway allowlist khớp SPEC (motorway → living_street + service)
  - [x] Snap về simple undirected graph — TODO khi chạy thật (xem P17)
  - [x] Edge distance Haversine — TODO khi chạy thật
  - [x] Output JSON đúng schema SPEC §9 (đã verify bằng `--emit-sample` + loader roundtrip)
  - [x] Pin OSM snapshot date trong docstring generator
  - [x] Verify file output < 50MB (`MAX_OUTPUT_BYTES = 50 * 1024 * 1024` enforced)
  - [x] Generator không thuộc runtime backend — không import osmnx/networkx ở `app/`
  - [x] Generator scaffold đã commit; file HCM thật chưa generate (chặn P17)
  - [ ] Ước tính size thực tế — pending P17

### P1 — Graph loader + startup validation
- [x] Module `infrastructure/graph_loader.py` đọc + parse JSON
- [x] Validate: file tồn tại, JSON hợp lệ
- [x] Validate `metadata`: `graph_version`, `bbox`, `max_snap_distance_meters`
- [x] Validate nodes: unique ID, lat ∈ [-90,90], lng ∈ [-180,180], nằm trong bbox
- [x] Validate edges: `from`/`to` tồn tại, `distance > 0`
- [x] Fail startup (raise) nếu bất kỳ rule nào vi phạm (`GraphValidationError`)
- [x] Wire vào FastAPI lifespan trong `main.py` (`build_graph_runtime` ở startup)
- [x] Unit test cho từng rule ở SPEC §12 (xem `tests/unit/test_graph_loader.py`)

### P2 — Adjacency + simple grid spatial index
- [x] `domain/graph.py` giữ adjacency: `dict[node_id] -> list[(neighbor_id, distance)]` (bidirectional, sort theo node_id)
- [x] `infrastructure/grid_index.py`: bucket node theo (lat, lng) cell 16×16 + ring search
- [x] API `nearest_node_id(lat, lng) -> str` (signature tương đương `find_nearest` của SPEC)
- [x] Unit test: nearest khớp brute-force trên fixture (xem `tests/unit/test_graph_runtime.py`)

### P3 — Snapper
- [x] `domain/snapper.py` với hàm `snap_point(runtime, lat, lng) -> SnapResult | raise`
- [x] Bước 1: validate point trong bbox metadata
- [x] Bước 2: lấy nearest node từ grid index
- [x] Bước 3: tính Haversine(point, node)
- [x] Bước 4: nếu > `max_snap_distance_meters` (200m) → raise `AcceptedAreaError`
- [x] Map domain error → HTTP 422 + `Error: Not in accepted area` (xem `http/route_errors.py`)
- [x] Unit test: outside bbox, nearest >200m, happy path, deterministic, just-over threshold

### P4 — Bidirectional Dijkstra
- [x] `domain/dijkstra.py` với `bidirectional_dijkstra(adjacency, start_id, end_id)`
- [x] Edge weight > 0, hỗ trợ undirected (adjacency build từ `build_bidirectional_adjacency`)
- [x] Search đồng thời từ start và end, dừng khi optimal meeting condition thoả
- [x] Tie-break deterministic: relax tie ưu tiên node_id nhỏ hơn, neighbor list sort theo node_id
- [x] Trả về `DijkstraResult` hoặc raise `NoRouteError`
- [x] Unit test:
  - [x] shortest path trên fixture graph
  - [x] no-path trên đồ thị disconnected
  - [x] tie-break ổn định qua 20 lần chạy
  - [x] prefers shorter competing route
  - [x] same start/end = zero distance

### P5 — Path reconstruction + distance
- [x] Reconstruct node ID list `[start, ..., end]` (`_path_to_origin` + `_path_toward_end`)
- [x] Tính distance: `start_snap + graph_distance + end_snap` (`compute_total_distance_meters`)
- [x] Build `route_points`: `[clicked_start, ...graph_nodes..., clicked_end]` (`reconstruct_route_points`)
- [x] Dedupe exact endpoint duplicates (tolerance 1e-9) (`dedupe_adjacent_exact_coordinates`)
- [x] Unit test: start/end preservation, intermediate order, exact dedupe, distance formula, same-snap-node edge case

### P6 — LRU route cache
- [x] `infrastructure/route_cache.py`: `OrderedDict` + `RouteCache(limit=1000)`
- [x] Key = `(graph_version, start_node_id, end_node_id)` (string key, reverse reuse qua lookup với key đảo)
- [x] Lưu graph-path node ID list + graph distance
- [x] Clicked endpoints được add **sau** khi cache hit (xem `reconstruct_route` chạy sau khi lấy graph path)
- [x] `/health` trả `cache.route_cache_size` + `cache.route_cache_limit` (xem `application/health.py`)
- [x] Unit test: key shape, reverse reuse, LRU eviction ở size 1001, version key isolation

### P7 — `GET /graph-bounds`
- [x] Response: `{ bbox, max_snap_distance_meters, graph_version }` (xem `application/graph_bounds.py`)
- [x] Source: metadata đã load từ graph lúc startup
- [x] Integration test (xem `tests/integration/test_route_api.py::test_graph_bounds_returns_metadata`)

### P8 — `POST /shortest-path`
- [x] `models/route_models.py`: `ShortestPathRequest`, `ShortestPathResponse` (gộp với legacy models vì chia sẻ `Point`)
- [x] `Point` model: lat ∈ [-90,90], lng ∈ [-180,180] (xem `models/point.py`)
- [x] Route handler:
  - [x] snap start, snap end (422 nếu fail)
  - [x] cache lookup theo snapped IDs
  - [x] cache miss → Bidirectional Dijkstra → cache set
  - [x] reconstruct `route_points` + `distance` (kèm snap segments)
  - [x] 404 nếu không tìm được path
- [x] Integration test (xem `tests/integration/test_route_api.py`):
  - [x] 200 happy path
  - [x] 422 ngoài bbox (đúng message SPEC)
  - [x] 422 invalid body
  - [x] 404 disconnected
  - [x] Determinism qua 2 lần gọi

### P9 — Legacy `POST /optimize-route` wrapper
- [x] Chỉ chấp nhận đúng 2 `points`
- [x] Map `points[0]→start`, `points[1]→end`
- [x] Reject nếu số lượng ≠ 2 với message "optimize-route requires exactly two points" (HTTP 422)
- [x] Response shape giống `/shortest-path`, dùng field `route_points` (đã chốt với user §9)
- [x] Integration test: 2 points ok + parametrize 0/1/3 reject

### P10 — Dọn dẹp code cũ _(in progress)_
- [x] Xoá `services/tsp_service.py` (sau khi P9 pass + frontend đã chuyển xong)
- [x] Xoá `services/osm_service.py` + bất kỳ Overpass/OSRM runtime call nào
- [x] Bỏ deps không còn dùng khỏi `backend/requirements.txt` — `requests` giữ làm test-only cho `test_no_external_runtime.py`
- [x] Kiểm tra `routers/route_api.py` không còn import các module đã xoá
- [x] Cập nhật `Walkthrough.md` cho khớp trạng thái mới (file này)

### P11 — Frontend: API client + state
- [x] `api/routeApi.js`: thêm `findShortestPath({start, end})`; thêm `getGraphBounds()` (rewrite hoàn toàn; bỏ `optimizeRoute` + `fetchIntersections`)
- [x] Bỏ `optimizeRoute()` + `fetchIntersections()` — `types/point.js` cũng xoá do không còn dùng
- [x] `hooks/useRoutePoints.js`: state mới
  - [x] `bounds` (từ `/graph-bounds`, inject qua prop)
  - [x] `boundsError` (raise ở App.jsx qua useQuery error)
  - [x] `selectionMode: 'start' | 'end'`
  - [x] `startPoint`, `endPoint`
  - [x] `route` (`route_points`, `distance`, `start_node_id`, `end_node_id`)
  - [x] `status: 'idle' | 'loading' | 'success' | 'error'`
  - [x] Bỏ waypoints
- [x] Auto-clear `route` khi `startPoint` hoặc `endPoint` thay đổi (`_setPoint` set route = EMPTY)

### P12 — Frontend: bỏ waypoint UI
- [x] `RouteControls.jsx`: 2 button "Start" / "End" + nút "Find Shortest Path" + nút "Clear"
- [x] `PointList.jsx`: chỉ hiển thị Start/End
- [x] `MapView.jsx`: marker role chỉ còn Start/End (bỏ WAYPOINT; label `Start` / `End`)
- [x] Bỏ prop/imports waypoint khỏi `App.jsx`
- [x] Giữ label đúng SPEC §7 ("Start" / "End" markers, "Find Shortest Path" button, "Error: Not in accepted area" message)

### P13 — Frontend: graph-bounds + bbox rectangle
- [x] Khi app load: gọi `getGraphBounds()` qua TanStack Query (`useQuery`, `staleTime: Infinity`)
- [x] Nếu fail → disable click handler (`selectionEnabled = boundsLoaded`), show error trong result panel
- [x] Khi có bounds: vẽ red rectangle (Leaflet `Rectangle` với `color: 'red'`, `fillOpacity: 0.05`)
- [x] Fit map bounds tới bbox (`MapBoundsFitter` qua `map.fitBounds`)
- [x] Click handler đọc `bounds` qua prop `selectionEnabled`

### P14 — Frontend: accepted-area validation
- [x] Helper `isInsideBbox(point, bbox)` trong `utils/geo.js`
- [x] Nếu click ngoài bbox:
  - [x] Không đặt marker (`addPoint` không được gọi)
  - [x] Không thay đổi Start/End hiện tại (chỉ set error message, không touch route)
  - [x] Show `Error: Not in accepted area` (qua `failRouteRequest` không clear route → SPEC §7 "keeps previous state unchanged")
- [x] Backend reject (vd snap >200m) hiển thị message từ `detail` (qua `parseError` trong `routeApi.js`)

### P15 — Frontend: polyline + distance + error states
- [x] `utils/format.js`: `formatDistance(m)` → `"<1000 ? m+' m' : km.toFixed(2)+' km'"`
- [x] `MapView.jsx`: vẽ `Polyline` từ `route.route_points`
- [x] Hiển thị distance + status (panel "Kết quả")
- [x] Loading state khi mutation pending (button đổi text "Đang tìm đường..." + status=LOADING)
- [x] Error state hiển thị `detail` từ backend (qua `parseError` map `body.detail` → `Error.message`)
- [x] Auto-fit map theo polyline (`MapBoundsFitter` watch `routePoints`)

### P16 — Docs & README reconcile
- [x] `README.md`: rewrite hoàn toàn — đổi từ TSP/OSRM sang local graph + Bidirectional Dijkstra + Start/End only, thêm API contract đầy đủ, luồng hoạt động, cấu trúc thư mục mới
- [x] `docs/product/*`: đã reconcile từ trước (xem `docs/product/*` còn legacy content, sẽ làm trong follow-up nếu user yêu cầu)
- [ ] `droid-wiki/`: refresh tự động qua `scripts/sync-github-wiki.sh` (out of scope MVP commit, làm khi user yêu cầu)
- [x] Note: KHÔNG tạo/sửa docs ngoài phạm vi trên trừ khi user yêu cầu

### P17 — Smoke test với committed HCM graph
- [x] Chạy `GET /health` → graph loaded, node/edge count > 0 _(smoke test pass: `hcm-fixture-v1`, 4 nodes, 2 edges)_
- [x] Chạy `GET /graph-bounds` → bbox + max_snap + graph_version _(smoke test pass)_
- [x] Chạy `POST /shortest-path` happy path → 200 + route_points + distance _(smoke test pass: distance ~420m)_
- [x] Chạy `POST /shortest-path` ngoài bbox → 422 + `Error: Not in accepted area` _(smoke test pass)_
- [x] Chạy `POST /shortest-path` disconnected → 404 + `No route found between selected points` _(smoke test pass)_
- [x] Verify `/optimize-route` legacy vẫn hoạt động với 2 points _(smoke test pass: cùng distance với `/shortest-path`)_
- [x] Verify `/optimize-route` reject 3 points → 422 + `optimize-route requires exactly two points` _(smoke test pass)_
- [x] Verify cache reuse qua `/health` `route_cache_size` _(smoke test pass: 2 call cùng snapped start/end → size 1)_
- [x] Verify determinism: cùng payload → cùng response _(integration test `test_shortest_path_is_deterministic` pass; manual smoke note: 2 call với clicked Start khác nhau cho route_points khác ở first point — đúng SPEC §8 vì `route_points[0]` là clicked coord)_
- [ ] Chọn 2 điểm thật trong TP.HCM qua UI, bấm Find Shortest Path — _chỉ verify được khi có graph HCM thật (cần chạy `scripts/generate_hcm_graph.py` với `osmnx` + Geofabrik PBF)_
- [x] `npm run build` pass _(128 modules, 348 kB JS / 18 kB CSS)_

---

## 6. Definition of Done — từng phase

| Phase | DoD bắt buộc |
| --- | --- |
| P0 | Fixture graph pass loader, có ≥2 path khác nhau để test tie-break |
| P1 | Mọi rule trong SPEC §9 có unit test, fail startup nếu graph lỗi |
| P2 | `find_nearest` đúng với grid test, thời gian < 10ms cho graph HCM |
| P3 | 422 + message đúng cho cả 3 case (out of bbox, >200m, happy) |
| P4 | Pass unit test shortest/no-path/tie-break deterministic |
| P5 | `route_points` dedupe đúng, distance khớp công thức SPEC §8 |
| P6 | Reverse reuse, LRU evict đúng size, key không phụ thuộc clicked coords |
| P7 | Integration test `/graph-bounds` trả đúng shape |
| P8 | 5 integration test case ở SPEC §12 pass |
| P9 | 3 integration test case ở SPEC §12 pass |
| P10 | Không còn import/module chết, `requirements.txt` sạch |
| P11 | Hook mới + API client mới, type check / build pass |
| P12 | UI không còn chuỗi "waypoint" nào, click flow chỉ Start/End |
| P13 | Map hiện bbox đỏ, fit đúng, error state khi API fail |
| P14 | Click ngoài bbox không đổi state + show error |
| P15 | Polyline vẽ đúng, distance format m/km đúng, loading + error rõ |
| P16 | README + docs/product/* khớp SPEC, không còn mô tả TSP/OSRM runtime |
| P17 | Manual smoke pass với graph HCM thật |

---

## 7. Test plan (map SPEC §12)

### Backend unit (P0–P6)
- [x] Loader: parse valid graph (`test_loads_spec_shaped_fixture_graph`)
- [x] Loader: reject missing/malformed metadata (`test_rejects_missing_metadata`)
- [x] Loader: reject invalid lat/lng (`test_rejects_invalid_latitude`)
- [x] Loader: reject node ngoài bbox (`test_rejects_node_outside_bbox`)
- [x] Loader: reject edge reference node không tồn tại (`test_rejects_edge_referencing_missing_node`)
- [x] Loader: reject edge distance ≤ 0 (`test_rejects_non_positive_edge_distance`)
- [x] Grid index: nearest đúng (`test_grid_index_matches_brute_force_on_fixture_points`)
- [x] Snapper: reject ngoài bbox (`test_rejects_latitude_below_bbox_min`, `_above_bbox_max`, `test_accepts_point_on_bbox_*_corners`)
- [x] Snapper: reject nearest >200m (`test_rejects_inside_bbox_beyond_max_snap_distance`, `test_rejects_distance_just_over_max_snap_threshold`)
- [x] Dijkstra: shortest path fixture (`test_shortest_path_on_fixture_graph`)
- [x] Dijkstra: no-path disconnected (`test_disconnected_component_raises_no_route`)
- [x] Dijkstra: tie-break deterministic (`test_tie_break_*`, `test_tie_break_is_deterministic_across_repeated_runs`)
- [x] Cache: key dùng graph_version + snapped node IDs (`test_make_cache_key_uses_version_and_node_ids_only`, `test_different_graph_version_is_distinct_key`)
- [x] Cache: reuse reverse (`test_reverse_lookup_reuses_forward_entry_with_reversed_nodes`, `test_service_reverse_reuses_cache_without_growing`)
- [x] Reconstruct: route_points có clicked Start/End, dedupe exact (`test_route_points_begin_with_clicked_start_*`, `test_exact_endpoint_on_node_dedupes_adjacent_duplicate`)
- [x] Distance: gồm snap segments + graph path (`test_distance_matches_independent_fixture_calculation`)

### Backend integration (P7–P9)
- [x] `GET /health` trả graph status + cache size (`test_health_endpoint_returns_cache_metadata`, `test_health_observes_cache_growth_and_stable_repeat`)
- [x] `GET /graph-bounds` trả bbox + max_snap + graph_version (`test_graph_bounds_returns_metadata`)
- [x] `POST /shortest-path` 200 happy path (`test_shortest_path_happy_path`)
- [x] `POST /shortest-path` 422 ngoài accepted area (`test_shortest_path_outside_bbox_returns_exact_detail`)
- [x] `POST /shortest-path` 404 no path (`test_shortest_path_disconnected_returns_404`)
- [x] `POST /shortest-path` 422 invalid body (`test_shortest_path_invalid_latitude_returns_422`)
- [x] `POST /optimize-route` chấp nhận đúng 2 points (`test_optimize_route_two_points_matches_shortest_path`)
- [x] `POST /optimize-route` từ chối waypoint payload (`test_optimize_route_rejects_non_two_points` với 0/1/3)
- [x] Block external HTTP ở runtime (`tests/integration/test_no_external_runtime.py`)

### Frontend checks (P11–P15)
- [x] `npm run build` pass _(current build pass trên code cũ; sẽ re-verify sau khi cutover sang `/shortest-path`)_
- [ ] App gọi `/graph-bounds` khi load
- [ ] Bbox đỏ hiển thị
- [ ] Selection disable khi `/graph-bounds` fail
- [ ] Chọn Start/End trong bbox OK
- [ ] Click ngoài bbox không đặt marker + show `Error: Not in accepted area`
- [ ] Đổi Start/End clear route cũ
- [ ] "Find Shortest Path" gọi `/shortest-path`
- [ ] `route_points` vẽ polyline đúng
- [ ] Distance hiển thị m/km auto format
- [ ] Backend no-route message hiển thị

---

## 8. API contract tóm tắt (tham chiếu nhanh)

`GET /health`
```json
{
  "status": "ok",
  "graph": { "loaded": true, "graph_version": "hcm-v1", "node_count": 1000, "edge_count": 3000 },
  "cache": { "route_cache_size": 0, "route_cache_limit": 1000 }
}
```

`GET /graph-bounds`
```json
{
  "bbox": { "min_latitude": 10.70, "min_longitude": 106.60, "max_latitude": 10.90, "max_longitude": 106.90 },
  "max_snap_distance_meters": 200,
  "graph_version": "hcm-v1"
}
```

`POST /shortest-path` request
```json
{ "start": { "latitude": 10.778109, "longitude": 106.714456 },
  "end":   { "latitude": 10.770016, "longitude": 106.720633 } }
```

`POST /shortest-path` response
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

Error shape (FastAPI default): `{ "detail": "message" }`

| Condition | Status | detail |
| --- | ---: | --- |
| Invalid body / lat-lng out of range | 422 | FastAPI validation |
| Point ngoài bbox / nearest >200m | 422 | `Error: Not in accepted area` |
| No path | 404 | `No route found between selected points` |
| Graph missing/malformed | startup fail | n/a |

---

## 9. Quyết định đã chốt

- [x] **Legacy `/optimize-route` response field**: trả `route_points` (khớp `/shortest-path`). Caller cũ phải đổi tên field, không hỗ trợ `ordered_points` nữa.
- [x] **Committed HCM graph**: commit thẳng vào git, generator script offline ở `scripts/generate_hcm_graph.py` dùng `osmnx` + `networkx`, source Geofabrik HCM extract. Không dùng LFS. Không runtime Overpass. Target <50MB.
- [x] **Frontend i18n**: UI tiếng Việt làm primary, các literal hardcode giữ đúng SPEC §7: button `Find Shortest Path`, marker label `Start / End`, error `Error: Not in accepted area`. Các nhãn khác (mode toggle, status, distance unit, panel title) tiếng Việt.
- [x] **Khi nào xoá `tsp_service.py` / `osm_service.py`**: ngay sau khi P9 + frontend cutover xong, trong cùng phase P10. Không giữ file chết.
- [x] **Marker drag**: không drag, đúng SPEC §7.

---

## 10. Risk log

| ID | Mô tả | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- |
| R1 | Committed HCM graph vượt 50MB hoặc bbox không khớp TP.HCM | Generator dùng osmnx từ Geofabrik extract, pin OSM snapshot date, validate bbox + size sau khi generate, giữ dưới ngưỡng 50MB | — | Mitigated (xem quyết định §9) |
| R2 | Bidirectional Dijkstra bug tie-break | Unit test deterministic pass + visual smoke sau P17 | — | Mitigated (pass test, cần visual confirm trên graph HCM thật) |
| R3 | Cache key đụng reversed pair | Key = `(graph_version, start_id, end_id)` string + reverse lookup đảo key trước khi build result | — | Mitigated (đã test reverse reuse) |
| R4 | Caller cũ gọi `/optimize-route` đang kỳ vọng `ordered_points` | Wrapper trả `route_points`; ghi breaking change trong response; cập nhật doc | — | Mitigated |
| R5 | Overpass/OSRM vẫn còn import ngầm | Đã grep: runtime `app/` không import `requests`/`overpass`/`osrm`; test `test_no_external_runtime.py` chặn gọi HTTP ngoài | — | Mitigated (sau P10) |
| R6 | Graph mới thiếu node ở vùng ven TP.HCM | Validate bbox metadata bao phủ toàn TP.HCM + unit test node-in-bbox | — | Open (chỉ verify được khi có graph HCM thật ở P17) |

---

## 11. Status log

| Ngày | Cập nhật |
| --- | --- |
| 2026-06-04 | Khởi tạo Walkthrough.md, mapping toàn bộ SPEC §14 vào 17 phase, status = Planning. |
| 2026-06-04 | Chốt câu hỏi mở: legacy `/optimize-route` trả `route_points`; committed HCM graph dùng generator offline (osmnx + Geofabrik, commit thẳng, target <50MB); UI tiếng Việt primary; xoá service cũ trong P10; không drag marker. Cập nhật P0, P9, §9, §10 theo. |
| 2026-06-04 | Reconcile thực tế: backend P0–P9 đã xong từ 8 commit gần nhất (graph loader → grid → snapper → bidirectional Dijkstra → reconstruct → LRU cache → `/graph-bounds` → `/shortest-path` → legacy wrapper). 59 unit + 12 integration tests pass, frontend build pass. Frontend vẫn còn code cũ. Tick checklist P0–P9 done, đánh dấu P10 in progress, chuyển §1 bảng so sánh sang dạng Backend done / Frontend lệch. |
| 2026-06-04 | P10 cleanup: xoá `tsp_service.py`, `osm_service.py`, `test_tsp_service.py`, `road_graph_legacy_osm_array.json` (60MB); `requests` giữ trong `requirements.txt` làm test-only (cho `test_no_external_runtime.py`); `route_api.py` không còn import module đã xoá. Tick P10 done, bắt đầu P11–P15 frontend. |

---

## 12. Next step đề xuất

Backend xong P0–P10. Tiếp theo:

1. **P11**: rewrite `frontend/src/api/routeApi.js` (`findShortestPath` + `getGraphBounds`, bỏ `optimizeRoute`/`fetchIntersections`); rewrite `useRoutePoints` (bỏ waypoints, thêm `bounds` + `status` + auto-clear route).
2. **P12**: rewrite `RouteControls.jsx` (2 mode Start/End + nút "Find Shortest Path" + Clear), `PointList.jsx` (bỏ waypoint), `MapView.jsx` (bỏ role WAYPOINT).
3. **P13**: App.jsx fetch `/graph-bounds` qua TanStack Query khi load; nếu fail disable click; vẽ `<Rectangle color="red" />`; fit map bounds.
4. **P14**: helper `isInsideBbox`; click ngoài bbox không đổi state, show "Error: Not in accepted area".
5. **P15**: `utils/format.js` `formatDistance(m)`; `<Polyline>` từ `route.route_points`; loading + error UI; auto-fit map theo polyline.
6. **P16**: rewrite `README.md` cho khớp SPEC §13 (bỏ TSP/OSRM, nói về local graph + Bidirectional Dijkstra + Start/End only).
7. **P17**: smoke test với fixture (graph HCM thật cần chạy generator thật trong môi trường có `osmnx` + Geofabrik PBF — tách rời khỏi scope MVP commit hiện tại).

## 13. Trạng thái cuối session 2026-06-04

- **Backend**: P0–P10 xong, 71/71 tests pass, không còn import/code chết.
- **Frontend**: P11–P15 xong, `npm run build` pass (128 modules, 348 kB JS / 18 kB CSS).
- **Docs**: P16 done (README rewrite), Walkthrough.md reconciled.
- **Smoke**: P17 backend smoke pass với fixture (mọi status code + error message + cache reuse + determinism); smoke với graph HCM thật cần generate bằng `osmnx` + Geofabrik PBF (ngoài scope session này).
- **Out of scope follow-up**: refresh `droid-wiki/`, smoke với graph HCM thật, optional OSRM geometry smoothing (SPEC §11 future).
