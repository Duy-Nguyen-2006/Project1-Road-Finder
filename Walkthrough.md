# Road Finder — Walkthrough & Progress Tracker (VRP Delivery Routing)

> Living document theo dõi tiến độ dự án VRP Delivery Routing. Mục tiêu cuối
> cùng: web app tối ưu giao vận đa-shipper (assignment / tour / fleet) trên
> local HCM road graph (directed, có `oneway` + `road_type`).
>
> - Spec nguồn: SPEC §1–§15
> - Cập nhật cuối: 2026-06-18
> - Trạng thái: **Backend (P0–P10) done, VRP layer (P11–P13) done, docs reconcile + harness-cli (P14) in progress, smoke thật (P15) pending**

---

## 0. Quy ước đọc file này

- Mỗi task là một checkbox `[ ]` / `[x]`.
- Tick `[x]` chỉ khi task đã xong **và** đã pass gate kiểm thử tương ứng.
- Phase chỉ "Done" khi **tất cả** task con tick xong **và** Definition of Done của phase đó pass.
- Nếu một task phát sinh rủi ro, ghi vào **§9 Risk log**.
- Mỗi khi đổi trạng thái, cập nhật **§10 Status log** (ngày + 1 dòng mô tả).

---

## 1. Tổng quan hiện trạng vs mục tiêu

| Hạng mục | Backend (đã làm) | Frontend (đã làm) | Mục tiêu (VRP) |
| --- | --- | --- | --- |
| Health | `GET /health` ✅ (graph + cache) | không dùng trong flow | `{status, graph, cache}` |
| Bounds | `GET /graph/bounds` ✅ (path `/graph/bounds`) | TanStack Query + red rectangle | Từ `/graph/bounds`, vẽ red rectangle |
| Route 1-điểm | `POST /route` ✅ | exposed ở `routeApi.postRoute` (FE không gọi) | 1 điểm → 1 điểm, `route_points` + `distance` |
| Assignment | `POST /assignments` ✅ | exposed ở `postAssignments` (FE không gọi) | 1 đơn + N shipper → ranking + recommended |
| Tour (TSP) | `POST /tours` ✅ | exposed ở `postTours` (FE không gọi) | 1 shipper + N đơn → 1 tour tối ưu |
| Fleet (VRP) | `POST /fleet` ✅ | TanStack Mutation, nút "Tối ưu đội" | M shipper + N đơn → M tour + unassigned |
| Algorithm | Bidirectional Dijkstra directed + CostMatrix + Assignment + TSP + VRP | n/a | Same |
| Graph nguồn | `road_graph.json` fixture `hcm-fixture-v2` (6 node / 5 cạnh, có oneway + road_type) | n/a | committed, < 50MB |
| Geometry | Local graph edges ✅ | polyline mỗi shipper | Local graph edges (OSRM optional) |
| Cost model | multiplier theo road_type + `avoid_road_types` / `avoid_edge_ids` | OptionsPanel checkboxes | Edge cost = distance × multiplier |
| Snap rule | local graph + 200m + 422 ✅ | bbox check ở click handler | Snap về node local graph, max 200m, reject nếu vượt |
| Cache | LRU 1000, key = `(graph_version, options_hash, src, dst)` | n/a | LRU 1000, share giữa /route, /tours, /fleet |
| UI mode | n/a | 3 mode (Order-Pickup / Order-Dropoff / Shipper) | Same |
| State | n/a | `useVrpState` (orders, shippers, fleetResult, status, avoidRoadTypes) | Same |
| Error ngoài bbox | 422 + `Error: Not in accepted area` ✅ | hiển thị message qua `parseError` | Same |
| Harness | n/a | n/a | `scripts/bin/harness-cli` v0.1.10 + `harness.db` schema v5 |

---

## 2. Mục tiêu cuối cùng (lấy từ SPEC §1, §3, §6)

Người dùng mở web, chọn nhiều đơn hàng (mỗi đơn có pickup + dropoff) và
nhiều shipper trong bbox đỏ TP.HCM, tùy chọn avoid_road_types, bấm **Tối
ưu đội**. Backend chạy Bidirectional Dijkstra trên local graph có hướng
(directed, `oneway` + `road_type`), tính CostMatrix, rồi assignment / TSP /
VRP tùy flow. Frontend vẽ polyline màu theo shipper + auto-fit map, hiển thị
`tổng quãng đường đội` auto-format `m` / `km`, list `ordered_stops` cho
từng shipper, section `Đơn chưa gán` nếu có `unassigned_order_ids`.

**In scope:** 4 flow (route, assignments, tours, fleet), local graph directed,
CostMatrix + LRU cache, snap + reconstruct với dedupe, OptionsPanel, màu theo
shipper, error states (`Error: Not in accepted area`, `No route found between
selected points`).

**Out of scope (MVP):** OSRM geometry smoothing, drag marker, real-time
re-route khi shipper di chuyển, turn-by-turn navigation, traffic, accounts,
saved routes, mobile-native behavior.

---

## 3. Cấu trúc hiện tại của repo

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
│   │   ├── models/
│   │   │   ├── point.py
│   │   │   └── route_models.py                  # route/assignment/tour/fleet DTOs
│   │   ├── routers/route_api.py                 # 6 endpoints
│   │   ├── services/
│   │   │   ├── leg_builder.py                   # snap-aware leg builder
│   │   │   ├── route_computation.py             # /route pipeline
│   │   │   ├── shortest_path_service.py         # cache-aware Dijkstra wrapper
│   │   │   └── tour_response_builder.py         # /tours + /fleet + /assignments leg builder
│   │   ├── utils/distance.py                    # Haversine (km + meters)
│   │   └── data/road_graph.json                 # fixture hcm-fixture-v2 (6/5)
│   ├── tests/                                   # 111 tests pass
│   │   ├── unit/                                # loader, dijkstra, snap, cache,
│   │   │                                        # reconstruct, runtime, cost_model,
│   │   │                                        # assignment, tsp, vrp, directed_graph
│   │   └── integration/                         # /health, /graph/bounds, /route,
│   │                                            # /assignments, /tours, /fleet,
│   │                                            # no_external_runtime
│   └── requirements.txt                         # fastapi, uvicorn, pydantic, requests (test-only)
├── frontend/
│   └── src/
│       ├── api/routeApi.js                      # getGraphBounds + postRoute + postAssignments + postTours + postFleet
│       ├── components/
│       │   ├── MapView.jsx                      # tile + bbox rectangle + shipper/order markers + tour polylines
│       │   ├── ModeSwitcher.jsx                 # Order ↔ Shipper
│       │   ├── OptionsPanel.jsx                 # avoid_road_types checkbox
│       │   ├── FleetResultPanel.jsx             # per-shipper tour + unassigned
│       │   └── PointList.jsx                    # order + shipper list
│       ├── hooks/useVrpState.js                 # state: orders, shippers, fleetResult, status, avoidRoadTypes
│       ├── utils/format.js                      # formatDistance (m/km)
│       ├── utils/geo.js                         # isInsideBbox, bboxToLeaflet
│       ├── App.jsx                              # useQuery bounds + useMutation fleet
│       ├── App.css
│       └── main.jsx
├── scripts/
│   ├── generate_hcm_graph.py                    # offline HCM graph generator scaffold
│   ├── bin/harness-cli                          # Rust CLI v0.1.10 (Harness v0 durable layer)
│   └── schema/                                  # harness schema migrations
├── docs/                                        # product/architecture/context rules + harness
│   ├── product/                                 # overview, routing, api, frontend-flow
│   ├── stories/                                 # US-XXX story packets (sẽ populate ở P14)
│   ├── templates/                               # story.md, decision.md, etc.
│   ├── decisions/                               # durable decision records
│   ├── ARCHITECTURE.md
│   ├── CONTEXT_RULES.md
│   ├── FEATURE_INTAKE.md
│   ├── HARNESS.md
│   ├── HARNESS_BACKLOG.md
│   ├── HARNESS_COMPONENTS.md
│   ├── HARNESS_MATURITY.md
│   ├── TEST_MATRIX.md
│   └── TRACE_SPEC.md
├── droid-wiki/                                  # generated wiki (out of git track, đồng bộ với code)
├── plans/
├── AGENTS.md                                    # agent operating shim (git Nexus + harness refs)
├── CLAUDE.md                                    # Claude shim (git Nexus + harness refs)
├── Walkthrough.md                               # file này
└── README.md                                    # quickstart + tổng quan
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
P6  LRU route cache
P7  GET /graph-bounds endpoint
P8  POST /route models + route
P9  Legacy /optimize-route wrapper (đúng 2 points) [đã xoá trong pivot VRP]
P10 Dọn dẹp code cũ (TSP/OSM/runtime deps)
--- pivot sang VRP ---
P11 Directed graph + cost model + snap service
P12 Assignment + TSP + VRP domain (brute-force + heuristic)
P13 CostMatrix + 3 endpoint mới (/assignments, /tours, /fleet)
P14 Docs reconcile (README, Walkthrough, product/*) + harness-cli + story packets
P15 Smoke thật trên HCM graph (cần osmnx + Geofabrik PBF) + E2E UI
```

---

## 5. Checklist chi tiết theo phase

### P0 — Graph schema & fixture ✅
- [x] Định nghĩa JSON schema (`metadata`, `nodes`, `edges`) khớp SPEC §9
- [x] Fixture `hcm-fixture-v2` (6 node / 5 cạnh, có oneway + road_type)
- [x] `graph_version` versioning (`hcm-fixture-v1`, `hcm-fixture-v2`, `hcm-v1`)
- [x] Generator scaffold: `scripts/generate_hcm_graph.py`
- [x] Highway allowlist: motorway → living_street + service
- [x] `MAX_OUTPUT_BYTES = 50 * 1024 * 1024` enforced
- [x] Generator không thuộc runtime backend — không import osmnx/networkx ở `app/`

### P1 — Graph loader + startup validation ✅
- [x] `infrastructure/graph_loader.py` đọc + parse + validate JSON
- [x] Validate: file tồn tại, JSON hợp lệ, `metadata`, `nodes`, `edges`
- [x] Fail startup nếu vi phạm bất kỳ rule nào

### P2 — Adjacency + simple grid spatial index ✅
- [x] `domain/graph.py`: directed adjacency + reverse
- [x] `infrastructure/grid_index.py`: 16×16 cell bucket + ring search
- [x] API `nearest_node_id(lat, lng) -> str`

### P3 — Snapper ✅
- [x] `application/snap_service.py`: bbox + grid + 200m
- [x] Map `AcceptedAreaError` → HTTP 422 + `Error: Not in accepted area`

### P4 — Bidirectional Dijkstra ✅
- [x] `domain/dijkstra.py`: forward + backward, deterministic tie-break
- [x] Hỗ trợ directed (oneway) qua `reverse_adjacency`
- [x] Unit test: shortest path, no-path, tie-break deterministic, same start/end

### P5 — Path reconstruction + distance ✅
- [x] `domain/route_reconstruction.py`: dedupe + distance formula
- [x] Reused cho `/route`, `/assignments`, `/tours`, `/fleet` qua `leg_builder`

### P6 — LRU route cache ✅
- [x] `infrastructure/route_cache.py`: LRU 1000, key = `(graph_version, options_hash, src, dst)`
- [x] `CostMatrix` reuse cache
- [x] Directed cache: không reuse reverse (oneway correct)
- [x] `/health` trả `cache.route_cache_size` + `cache.route_cache_limit`

### P7 — `GET /graph/bounds` ✅
- [x] Path: `/graph/bounds` (gạch chéo)
- [x] Response: `{ bbox, max_snap_distance_meters, graph_version }`

### P8 — `POST /route` ✅
- [x] `models/route_models.py`: `RouteRequest`, `RouteResponse`
- [x] Route handler: snap → cache → Bidirectional Dijkstra → reconstruct → 404 nếu fail
- [x] `options: RoutingOptions` optional

### P9 — Legacy `/optimize-route` ✅ (xoá trong pivot VRP)
- [x] Đã gỡ — pivot sang VRP thay thế

### P10 — Dọn dẹp code cũ ✅
- [x] Xoá `services/tsp_service.py`, `services/osm_service.py`
- [x] `requests` giữ test-only cho `test_no_external_runtime.py`
- [x] `routers/route_api.py` không còn import module đã xoá

### P11 — Directed graph + cost model + snap service ✅
- [x] `domain/cost_model.py`: `RoutingOptions` + `DEFAULT_ROAD_MULTIPLIERS`
- [x] `application/snap_service.py`: snap trả về `SnapResult(node_id, distance_meters)`
- [x] `domain/graph.py`: `build_directed_adjacency`, `build_reverse_adjacency` (oneway)
- [x] `domain/graph_types.py`: `GraphNode`, `GraphEdge`, `GraphMetadata`, `ValidatedGraph`
- [x] `domain/protocols.py`: `DistanceProvider`, `NodeCoordinateLookup`

### P12 — Assignment + TSP + VRP domain ✅
- [x] `domain/assignment.py`: `rank_shippers_for_order` (compute 2 leg per shipper)
- [x] `domain/tsp.py`: `Stop`, `Tour`, `optimize_tour` (brute-force ≤8 stops, NN + 2-opt lớn hơn)
- [x] `domain/vrp.py`: `solve_vrp` (cheapest-insertion + intra 2-opt + inter relocate, brute-force ≤3 đơn ≤2 shipper)
- [x] `services/tour_response_builder.py`: leg builder chung cho assignment/tour/fleet

### P13 — CostMatrix + 3 endpoint mới ✅
- [x] `application/cost_matrix.py`: many-to-many, cache reuse `RouteCache`
- [x] `POST /assignments`: rank shipper cho 1 đơn
- [x] `POST /tours`: 1 shipper + N đơn
- [x] `POST /fleet`: M shipper + N đơn
- [x] `services/route_computation.py`: pipeline `/route`
- [x] Frontend cutover: `useVrpState`, `ModeSwitcher`, `OptionsPanel`, `FleetResultPanel`, gọi `postFleet`
- [x] `b7afc10 feat: VRP fleet UI and directed routing fixes` (commit)
- [x] `02e98dd fix(routing): directed Dijkstra, clean arch, unified legs, lean API` (commit)
- [x] `a2bc8f4 chore: cosmetic cleanup after routing review` (commit)

### P14 — Docs reconcile + harness-cli + story packets (in progress)
- [x] `README.md` rewrite cho VRP (4 flow + 6 endpoint + cost model)
- [x] `docs/product/overview.md` rewrite cho VRP
- [x] `docs/product/routing.md` rewrite cho directed + cost model + 3 solver
- [x] `docs/product/api.md` rewrite cho 6 endpoint
- [x] `docs/product/frontend-flow.md` rewrite cho state + interactions
- [ ] `Walkthrough.md` reconcile (file này) ← in progress
- [x] `scripts/bin/harness-cli` install (v0.1.10)
- [x] `harness.db` init + schema v5
- [ ] Story packets trong `docs/stories/` cho 4 flow VRP
- [ ] Populate `docs/stories/backlog.md` (mở "TBD unsliced")
- [ ] Drop `axios` khỏi `frontend/package.json` (dep rác)
- [ ] Archive/xoá `Code.md` (3.7MB, nội dung i18n không liên quan)
- [ ] Archive/xoá `repomix-output.xml` (75KB, snapshot code phase cũ)
- [ ] Xoá `backend/Walkthrough.md` và `frontend/Walkthrough.md` (trùng với root)

### P15 — Smoke thật + E2E UI (pending, cần environment)
- [ ] Generate real HCM graph bằng `scripts/generate_hcm_graph.py` (cần `osmnx` + Geofabrik `vietnam-latest.osm.pbf`, expected ~50MB)
- [ ] Smoke test backend với graph HCM thật (≥1000 node)
- [ ] E2E UI: 2 shipper + 3 đơn trong TP.HCM thật, verify visual polyline + total_distance_meters
- [ ] Performance benchmark: < 200ms cho /fleet với 5 shipper + 10 đơn
- [ ] Visual smoke: mỗi shipper có 1 polyline riêng, color phân biệt, unassigned section

---

## 6. Definition of Done — từng phase

| Phase | DoD bắt buộc |
| --- | --- |
| P0 | Fixture graph pass loader, có ≥2 path khác nhau để test tie-break + cost multiplier |
| P1 | Mọi rule trong SPEC §9 có unit test, fail startup nếu graph lỗi |
| P2 | `nearest_node_id` đúng với grid test, thời gian < 10ms cho graph HCM |
| P3 | 422 + message đúng cho cả 3 case (out of bbox, >200m, happy) |
| P4 | Pass unit test shortest/no-path/tie-break deterministic + oneway correct |
| P5 | `route_points` dedupe đúng, distance khớp công thức SPEC §8 |
| P6 | LRU evict đúng size, key không phụ thuộc clicked coords, options_hash isolation |
| P7 | Integration test `/graph/bounds` trả đúng shape |
| P8 | 4 integration test case (200 / 422 bbox / 404 / 422 invalid) pass |
| P9 | [đã gỡ] |
| P10 | Không còn import/module chết, `requirements.txt` sạch |
| P11 | Cost model unit test, snap service không còn phụ thuộc snapper shim |
| P12 | Assignment ranking test, TSP brute-force vs heuristic test, VRP inter-relocate test |
| P13 | `/assignments`, `/tours`, `/fleet` integration test pass; FE build pass; FE gọi `/fleet` đúng shape |
| P14 | Docs khớp code 100%, harness-cli hoạt động, story packets cover 4 flow |
| P15 | Real HCM graph smoke + E2E UI pass với data thật |

---

## 7. Test plan (map SPEC §12)

### Backend unit (P0–P13)
- [x] Loader: parse valid graph + reject missing/malformed metadata + invalid lat/lng + node ngoài bbox + edge reference missing + edge distance ≤ 0
- [x] Grid index: nearest matches brute-force trên fixture
- [x] Snapper: reject ngoài bbox + reject >200m + happy path + corner cases
- [x] Dijkstra: shortest path + no-path + tie-break deterministic + oneway correct
- [x] Cost model: multiplier per road_type + avoid_road_types → inf
- [x] Cache: key dùng (graph_version, options_hash, src, dst) + version isolation + avoid reverse reuse (oneway)
- [x] Reconstruct: route_points begin with clicked + dedupe exact + distance formula
- [x] Assignment: ranking + feasible flag + recommended_shipper_id
- [x] TSP: brute-force ≤8 stops + NN + 2-opt + precedence
- [x] VRP: cheapest-insertion + intra 2-opt + inter relocate + brute-force ≤3 đơn ≤2 shipper + unassigned

### Backend integration (P7–P13)
- [x] `GET /health` trả graph + cache
- [x] `GET /graph/bounds` trả metadata
- [x] `POST /route` 200 / 422 bbox / 404 no-path / 422 invalid
- [x] `POST /assignments` ranking + recommended
- [x] `POST /tours` ordered_stops + legs + total + optimal
- [x] `POST /fleet` tours + unassigned + total + optimal
- [x] Block external HTTP ở runtime (`test_no_external_runtime.py`)

### Frontend checks (P13)
- [x] `npm run build` pass (130 modules, 352 kB JS)
- [x] App gọi `/graph/bounds` khi load
- [x] Bbox đỏ hiển thị
- [x] Selection disable khi `/graph/bounds` fail
- [x] Chọn Order (Pickup → Dropoff) trong bbox OK
- [x] Chọn Shipper trong bbox OK
- [x] Click ngoài bbox không đặt marker + show `Error: Not in accepted area`
- [x] Toggle mode giữa Order ↔ Shipper
- [x] OptionsPanel `avoid_road_types` toggle
- [x] "Tối ưu đội" gọi `/fleet` + vẽ polyline màu theo shipper
- [x] Hiển thị `total_distance_meters` m/km + `FleetResultPanel` per shipper
- [x] Hiển thị `unassigned_order_ids` nếu có
- [x] Backend no-route message hiển thị
- [x] Auto-fit map theo polylines

---

## 8. API contract tóm tắt (tham chiếu nhanh)

`GET /health` → `{ status, graph: { loaded, graph_version, node_count, edge_count }, cache: { route_cache_size, route_cache_limit } }`

`GET /graph/bounds` → `{ bbox, max_snap_distance_meters, graph_version }`

`POST /route` (req: `{ start, end, options? }`) → `{ route_points, distance }`

`POST /assignments` (req: `{ order, shippers, options? }`) → `{ recommended_shipper_id, ranking: [{ shipper_id, feasible, total_distance_meters, legs: [...] }] }`

`POST /tours` (req: `{ shipper, orders, options? }`) → `{ shipper_id, ordered_stops: [...], legs: [...], total_distance_meters, optimal }`

`POST /fleet` (req: `{ shippers, orders, options? }`) → `{ tours: [...], unassigned_order_ids, total_distance_meters, optimal }`

Error shape: `{ "detail": "..." }`. `Error: Not in accepted area` (422), `No route found between selected points` (404).

---

## 9. Quyết định đã chốt

- [x] **Project direction = VRP Delivery Routing** (multi-shipper, multi-order, directed graph). Pivot từ MVP Start/End ngày 2026-06-14.
- [x] **Directed graph**: edge có `oneway` + `road_type`. `build_directed_adjacency` cho forward, `build_reverse_adjacency` cho backward Dijkstra. Cache key không share reverse (oneway correct).
- [x] **Cost model**: `edge_cost = distance × multiplier(road_type)`. `avoid_road_types` → inf. `avoid_edge_ids` → inf. Multiplier default: `highway` 0.8, `trunk` 0.85, `primary` 0.9, `secondary` 1.0, `tertiary` 1.1, `residential` 1.2.
- [x] **Solver strategy**:
  - Assignment: rank theo tổng 2 leg (to_pickup + to_dropoff).
  - TSP: brute-force ≤8 stops (optimal), NN + 2-opt lớn hơn.
  - VRP: brute-force ≤3 đơn ≤2 shipper (optimal), cheapest-insertion + intra 2-opt + inter relocate lớn hơn.
- [x] **Committed HCM graph**: commit thẳng vào git, generator offline ở `scripts/generate_hcm_graph.py`. Target <50MB. Default `hcm-fixture-v2` cho test deterministic; `hcm-v1` cho data thật.
- [x] **Frontend i18n**: UI tiếng Việt primary. SPEC literal giữ EN: button "Tối ưu đội", marker color code, error `Error: Not in accepted area`. Label khác (mode toggle, status, distance unit, panel title) tiếng Việt.
- [x] **Marker drag**: không drag.
- [x] **Harness integration**: `scripts/bin/harness-cli` (Rust) là operational tool. `harness.db` local, `.gitignore`d. Schema v5 (gồm tool-registry, intervention, tool-extensions).
- [x] **Legacy removal**: `/shortest-path`, `/optimize-route`, `/graph-bounds` (gạch nối) đã xoá. `services/tsp_service.py`, `services/osm_service.py` đã xoá. `hooks/useRoutePoints.js`, `components/RouteControls.jsx` đã xoá.

---

## 10. Risk log

| ID | Mô tả | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- |
| R1 | Committed HCM graph vượt 50MB hoặc bbox không khớp TP.HCM | Generator dùng osmnx + Geofabrik, pin snapshot, validate bbox + size, giữ < 50MB | — | Open (chỉ verify khi có graph thật ở P15) |
| R2 | Bidirectional Dijkstra bug tie-break hoặc oneway | Unit test deterministic + visual smoke P15 | — | Mitigated (test pass) |
| R3 | Cache key đụng reversed pair hoặc ignore options | Key = `(graph_version, options_hash, src, dst)`; directed cache không share reverse | — | Mitigated |
| R4 | Caller cũ gọi `/optimize-route` đang kỳ vọng `ordered_points` | Endpoint xoá hoàn toàn; ghi breaking change trong `droid-wiki/lore.md` | — | Mitigated |
| R5 | Overpass/OSRM vẫn còn import ngầm | Runtime `app/` không import `requests`/`overpass`/`osrm`; test `test_no_external_runtime.py` chặn gọi HTTP ngoài | — | Mitigated |
| R6 | Graph mới thiếu node ở vùng ven TP.HCM | Validate bbox metadata bao phủ toàn TP.HCM + unit test node-in-bbox | — | Open (chỉ verify P15) |
| R7 | `Code.md` (3.7MB) và `repomix-output.xml` (75KB) stale content trong repo | Archive/xoá trong P14 | — | Open (P14) |
| R8 | `axios` dep thừa trong `frontend/package.json` | Drop trong P14 | — | Open (P14) |
| R9 | Docs (README, Walkthrough, product/*) lệch code qua pivot VRP | Reconcile trong P14 | — | In progress (P14) |
| R10 | Harness chưa có story packet cho 4 flow VRP | Tạo 4 story packet + populate backlog trong P14 | — | In progress (P14) |

---

## 11. Status log

| Ngày | Cập nhật |
| --- | --- |
| 2026-05-21 | Khởi tạo repo, khung Road Finder + docs sơ bộ (phase cũ: TSP + OSRM runtime) |
| 2026-06-04 | Cutover MVP: xoá `tsp_service`, `osm_service`; backend P0–P10 xong (graph loader → grid → snapper → Bidirectional Dijkstra → reconstruct → LRU cache → `/graph-bounds` → `/shortest-path`); FE chuyển sang `useRoutePoints` + 2 mode Start/End; 71/71 tests pass; FE build pass |
| 2026-06-14 | Pivot sang VRP: commit `b7afc10 feat: VRP fleet UI and directed routing fixes` — thêm assignment, tour, fleet API + directed routing + FE rewrite sang `useVrpState` + `ModeSwitcher` + `FleetResultPanel` + `OptionsPanel`; gọi `postFleet` |
| 2026-06-14 | Commit `02e98dd fix(routing): directed Dijkstra, clean arch, unified legs, lean API` — directed graph + `oneway` + `road_type`; xoá legacy `/shortest-path`, `/optimize-route`, `/graph-bounds`; tách `domain` thành cost_model/graph_types/protocols/assignment/tsp/vrp; unified leg shape giữa `/route` và `/fleet`; 5 endpoint `/health`, `/graph/bounds`, `/route`, `/assignments`, `/tours`, `/fleet` |
| 2026-06-14 | Commit `a2bc8f4 chore: cosmetic cleanup after routing review` — drop `ShortestPathResponse` (dùng `ComputedRoute`); xoá `domain/snapper` shim; `snap_service` dùng chung; cache `current_dist` trong TSP/VRP 2-opt |
| 2026-06-17 | Chạy `node .gitnexus/run.cjs analyze` — index 1,520 nodes, 2,720 edges, 34 clusters, 71 flows |
| 2026-06-18 | Reconcile docs: rewrite `README.md`, `docs/product/{overview,routing,api,frontend-flow}.md` cho VRP; install `scripts/bin/harness-cli` v0.1.10; init + migrate `harness.db` (schema v5); reconcile `Walkthrough.md` (file này) sang pivot VRP |

---

## 12. Next step đều xuất (sau P14)

1. Tạo 4 story packet trong `docs/stories/` cho 4 flow VRP: `/route`, `/assignments`, `/tours`, `/fleet`.
2. Populate `docs/stories/backlog.md`: thay "TBD unsliced" bằng E01 (VRP) epic với 4 story trên.
3. Drop `axios` khỏi `frontend/package.json`; archive/xoá `Code.md` và `repomix-output.xml`; xoá `backend/Walkthrough.md` + `frontend/Walkthrough.md` (trùng với root).
4. Generate real HCM graph (cần environment có `osmnx` + Geofabrik `vietnam-latest.osm.pbf` ~200MB) → commit file mới với `graph_version = hcm-v1`.
5. Smoke test backend với graph HCM thật (≥1000 node).
6. E2E UI smoke: 2 shipper + 3 đơn trong TP.HCM thật, verify visual polyline + total_distance_meters + unassigned section.
7. (Future) OSRM geometry smoothing, drag marker, traffic — theo SPEC §11.
