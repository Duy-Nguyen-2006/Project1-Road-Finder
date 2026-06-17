# API Contracts

Tất cả endpoint dùng JSON. Error shape mặc định của FastAPI:
`{ "detail": "..." }`. CORS mở `http://localhost:5173` (Vite dev).

Base URL: `http://localhost:8000` (override qua `VITE_API_BASE_URL` ở FE).

---

## GET /health

Smoke + monitor.

```json
{
  "status": "ok",
  "graph": { "loaded": true, "graph_version": "hcm-fixture-v2", "node_count": 6, "edge_count": 5 },
  "cache": { "route_cache_size": 0, "route_cache_limit": 1000 }
}
```

## GET /graph/bounds

Frontend gọi khi load (TanStack Query, `staleTime: Infinity`).

```json
{
  "bbox": { "min_latitude": 10.7, "min_longitude": 106.6, "max_latitude": 10.9, "max_longitude": 106.9 },
  "max_snap_distance_meters": 200,
  "graph_version": "hcm-fixture-v2"
}
```

## POST /route — 1 điểm → 1 điểm

### Request

```json
{
  "start":  { "latitude": 10.778109, "longitude": 106.714456 },
  "end":    { "latitude": 10.770016, "longitude": 106.720633 },
  "options": { "avoid_road_types": [], "avoid_edge_ids": [] }
}
```

### Response 200

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

### Errors

| Status | detail |
| ---: | --- |
| 422 | `Error: Not in accepted area` (point ngoài bbox / snap > 200m) |
| 404 | `No route found between selected points` |
| 422 | FastAPI validation (lat/lng out of range, body thiếu field) |

---

## POST /assignments — 1 đơn + N shipper → ranking

### Request

```json
{
  "order": {
    "id": "o1",
    "pickup":  { "latitude": 10.778109, "longitude": 106.714456 },
    "dropoff": { "latitude": 10.770016, "longitude": 106.720633 }
  },
  "shippers": [
    { "id": "s1", "location": { "latitude": 10.779000, "longitude": 106.715000 } },
    { "id": "s2", "location": { "latitude": 10.781000, "longitude": 106.717000 } }
  ],
  "options": { "avoid_road_types": ["highway"], "avoid_edge_ids": [] }
}
```

### Response 200

```json
{
  "recommended_shipper_id": "s1",
  "ranking": [
    {
      "shipper_id": "s1",
      "feasible": true,
      "total_distance_meters": 2500.0,
      "legs": [
        { "kind": "to_pickup",  "distance_meters": 800.0, "route_points": [...] },
        { "kind": "to_dropoff", "distance_meters": 1700.0, "route_points": [...] }
      ]
    },
    {
      "shipper_id": "s2",
      "feasible": true,
      "total_distance_meters": 3200.0,
      "legs": [ ... ]
    }
  ]
}
```

`feasible=false` (thường do 1 trong 2 leg disconnected) → `legs=[]`,
`total_distance_meters` = `sr.total_distance_meters` (có thể = inf).

---

## POST /tours — 1 shipper + N đơn → 1 tour (TSP)

### Request

```json
{
  "shipper": { "id": "s1", "location": { "latitude": 10.779000, "longitude": 106.715000 } },
  "orders": [
    { "id": "o1", "pickup": { "latitude": 10.778109, "longitude": 106.714456 }, "dropoff": { "latitude": 10.770016, "longitude": 106.720633 } },
    { "id": "o2", "pickup": { "latitude": 10.781000, "longitude": 106.717000 }, "dropoff": { "latitude": 10.782000, "longitude": 106.718000 } }
  ],
  "options": { "avoid_road_types": [], "avoid_edge_ids": [] }
}
```

### Response 200

```json
{
  "shipper_id": "s1",
  "ordered_stops": [
    { "order_id": "o1", "kind": "pickup",  "coordinate": { "latitude": 10.778109, "longitude": 106.714456 } },
    { "order_id": "o1", "kind": "dropoff", "coordinate": { "latitude": 10.770016, "longitude": 106.720633 } },
    { "order_id": "o2", "kind": "pickup",  "coordinate": { "latitude": 10.781000, "longitude": 106.717000 } },
    { "order_id": "o2", "kind": "dropoff", "coordinate": { "latitude": 10.782000, "longitude": 106.718000 } }
  ],
  "legs": [
    { "kind": "o1_pickup",  "distance_meters": 800.0,  "route_points": [...] },
    { "kind": "o1_dropoff", "distance_meters": 1700.0, "route_points": [...] },
    { "kind": "o2_pickup",  "distance_meters": 600.0,  "route_points": [...] },
    { "kind": "o2_dropoff", "distance_meters": 700.0,  "route_points": [...] }
  ],
  "total_distance_meters": 3800.0,
  "optimal": true
}
```

`optimal=true` khi `len(stops) ≤ 8` (brute-force chạy); `false` với NN+2-opt.

---

## POST /fleet — M shipper + N đơn → M tour + unassigned (VRP)

### Request

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

### Response 200

```json
{
  "tours": [
    {
      "shipper_id": "s1",
      "ordered_stops": [ ... ],
      "legs": [ ... ],
      "total_distance_meters": 2500.0,
      "optimal": false
    },
    {
      "shipper_id": "s2",
      "ordered_stops": [ ... ],
      "legs": [ ... ],
      "total_distance_meters": 1800.0,
      "optimal": false
    }
  ],
  "unassigned_order_ids": [],
  "total_distance_meters": 4300.0,
  "optimal": false
}
```

`optimal=true` khi `len(orders) ≤ 3` và `len(shippers) ≤ 2` (brute-force
chạy). Mỗi `tours[i].optimal` riêng lẻ = `True` khi tour đó dùng
`optimize_tour` brute-force (≤ 8 stops).

`unassigned_order_ids`: đơn không gán được (disconnected / inf cost ở cả
shipper, hoặc gặp vi phạm precedence ở tất cả assignment).
