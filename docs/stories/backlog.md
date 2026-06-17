# Story Backlog

Durable backlog cho project. Story packets thuộc `docs/stories/epics/<E-id>-<name>/<US-id>-<slug>.md`.
Khi một story được implement, link tới `docs/stories/epics/<E-id>/<US-id>.md` và cập nhật
proof status qua `scripts/bin/harness-cli story update --id <US-id> --unit 1 --integration 1 --e2e 0 --platform 0`.

## Active Epics

| Epic | Mô tả | Status |
| --- | --- | --- |
| [E01 — VRP Delivery Routing](epics/E01-vrp-delivery-routing/) | 4 flow: /route, /assignments, /tours, /fleet. Local HCM graph directed + CostMatrix + LRU cache + snap + reconstruct. Frontend `useVrpState` + `ModeSwitcher` + `OptionsPanel` + `FleetResultPanel`. | in_progress |

### E01 — VRP Delivery Routing

| ID | Title | Lane | Verify command | Unit | Integration | E2E | Platform |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [US-001](epics/E01-vrp-delivery-routing/US-001-post-route.md) | POST /route — 1 điểm → 1 điểm | normal | `cd backend && .venv/bin/python -m pytest tests/unit tests/integration -q` | 1 | 1 | 0 | 0 |
| [US-002](epics/E01-vrp-delivery-routing/US-002-post-assignments.md) | POST /assignments — 1 đơn + N shipper → ranking | normal | `cd backend && .venv/bin/python -m pytest tests/unit/test_assignment_tour.py tests/integration/test_route_api.py -q -k assignment` | 1 | 1 | 0 | 0 |
| [US-003](epics/E01-vrp-delivery-routing/US-003-post-tours.md) | POST /tours — 1 shipper + N đơn → 1 tour (TSP) | normal | `cd backend && .venv/bin/python -m pytest tests/unit/test_assignment_tour.py tests/integration/test_route_api.py -q -k tour` | 1 | 1 | 0 | 0 |
| [US-004](epics/E01-vrp-delivery-routing/US-004-post-fleet.md) | POST /fleet — M shipper + N đơn → M tour + unassigned (VRP) | normal | `cd backend && .venv/bin/python -m pytest tests/unit/test_vrp.py tests/integration/test_route_api.py -q -k fleet` | 1 | 1 | 0 | 0 |

## Backlog Items (friction / improvement)

| ID | Title | Pain | Risk | Status |
| --- | --- | --- | --- | --- |
| BL-001 | Drop `axios` dep thừa trong `frontend/package.json` | Code dùng `fetch`; `axios ^1.16.1` chỉ khai báo dep, không import runtime. Gây nhầm lẫn + bundle lớn hơn cần thiết. | tiny | open |
| BL-002 | Archive/xoá `Code.md` (3.7MB) trong repo root | File i18n tiếng Việt–Trung–Anh không liên quan, chỉ làm phình repo. | tiny | open |
| BL-003 | Archive/xoá `repomix-output.xml` (75KB) trong repo root | Snapshot code phase cũ (TSP/OSRM runtime), không còn khớp code hiện tại. Gây hiểu lầm. | tiny | open |
| BL-004 | Xoá `backend/Walkthrough.md` và `frontend/Walkthrough.md` | Trùng với root `Walkthrough.md`, chỉ tham chiếu phase cũ. | tiny | open |
| BL-005 | Generate real HCM graph bằng `scripts/generate_hcm_graph.py` | Hiện chỉ có fixture `hcm-fixture-v2` (6/5). Cần `osmnx` + Geofabrik `vietnam-latest.osm.pbf` để commit file thật `hcm-v1`. | normal | open |
| BL-006 | E2E smoke UI với 2 shipper + 3 đơn TP.HCM thật | Cần graph thật (BL-005) + agent-browser session. Verify visual polyline + total_distance_meters + unassigned section. | normal | open |
| BL-007 | Expose `brute_force_threshold` qua `RoutingOptions` config | Hiện hardcode ở `domain/tsp.py` (≤8) và `domain/vrp.py` (≤3 đơn ≤2 shipper). Có thể cần tune cho HCM graph lớn. | tiny | open |
| BL-008 | Ghi `docs/decisions/0008-vrp-pivot.md` cho pivot 2026-06-14 | Pivot MVP Start/End → VRP là thay đổi scope + API shape lớn; cần durable decision record. | tiny | open |
| BL-009 | Pin `graph_version` policy trong `scripts/generate_hcm_graph.py` | Hiện `--graph-version` flag tự do. Cần rule: `hcm-v1` cho data thật, `hcm-fixture-*` cho test. | tiny | open |

## Status Flow

```text
planned -> in_progress -> implemented
                  |
                  v
               changed
                  |
                  v
               retired
```

## Quy tắc thêm story

1. Tạo file `docs/stories/epics/E<NN>-<slug>/<US-NNN>-<slug>.md` từ
   `docs/templates/story.md`.
2. Link từ backlog này.
3. Khi implement xong, chạy verify command → cập nhật proof booleans
   bằng `scripts/bin/harness-cli story update --id <id> --unit 1 --integration 1 --e2e 0 --platform 0`.
4. Story `verify` tự chạy command và ghi `last_verified_at` +
   `last_verified_result`.
