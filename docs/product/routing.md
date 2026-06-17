# Routing

Road Finder dùng Bidirectional Dijkstra trên đồ thị có hướng (directed
graph) để tính tuyến đường ngắn nhất giữa 2 node. Cost model áp dụng
multiplier theo `road_type` và cho phép `avoid_road_types` / `avoid_edge_ids`
để né loại đường.

## Algorithm Choice

**Bidirectional Dijkstra** (forward trên directed adjacency + backward trên
reverse adjacency, tôn trọng `oneway`). Hỗ trợ deterministic tie-break
(parent ID nhỏ hơn thắng khi distance bằng nhau). Chạy `O((V+E) log V)`
nhưng thường visit ít node hơn 1 chiều.

Khi `start_node_id == end_node_id`: trả về `[start_node_id]` với
`graph_distance_meters = 0` (không chạy search).

Khi không tìm được path: raise `NoRouteError` → HTTP 404.

## Cost Model

```text
edge_cost(distance, road_type, options) = distance × multiplier(road_type)
```

Multiplier mặc định theo `road_type` (`app/domain/cost_model.py`):

| road_type | multiplier |
| --- | ---: |
| highway | 0.8 |
| trunk | 0.85 |
| primary | 0.9 |
| secondary | 1.0 |
| tertiary | 1.1 |
| residential | 1.2 |
| default | 1.0 |

`RoutingOptions`:

- `avoid_road_types: tuple[str, ...]` — cạnh thuộc type này có cost = `inf`
  (Dijkstra sẽ không đi qua).
- `avoid_edge_ids: tuple[str, ...]` — tương tự cho edge ID cụ thể.
- `tsp_brute_force_max_stops: int | None` — ngưỡng brute-force cho `optimize_tour`.
  Khi `len(stops) <= threshold` (default 8), solver thử mọi permutation
  (đảm bảo optimal). Set = 0 để tắt brute-force (luôn dùng NN + 2-opt).
  `None` nghĩa là dùng default.
- `vrp_brute_force_max_orders: int | None` — ngưỡng số đơn để trigger
  brute-force VRP (default 3). `solve_vrp` thử mọi `product(shipper_ids,
  repeat=len(orders))` khi `len(orders) <= threshold` AND
  `len(shippers) <= vrp_brute_force_max_shippers`.
- `vrp_brute_force_max_shippers: int | None` — ngưỡng số shipper cho
  brute-force VRP (default 2).

Mọi request đều nhận `options` (optional, default rỗng). Solver thresholds
cho phép caller tune tradeoff optimality vs response time khi input lớn.

## Graph Source

Local OSM-derived graph JSON ở `backend/app/data/road_graph.json` (committed,
< 50MB, hỗ trợ `oneway` + `road_type`).

Schema (`metadata` + `nodes` + `edges`):

```json
{
  "metadata": {
    "graph_version": "hcm-fixture-v2",
    "bbox": { "min_latitude": 10.7, "min_longitude": 106.6, "max_latitude": 10.9, "max_longitude": 106.9 },
    "max_snap_distance_meters": 200
  },
  "nodes": {
    "node-start": { "latitude": 10.778109, "longitude": 106.714456 }
  },
  "edges": [
    {
      "from": "node-start",
      "to": "node-mid",
      "distance": 120.5,
      "oneway": false,
      "road_type": "residential"
    }
  ]
}
```

Generator scaffold: `scripts/generate_hcm_graph.py` (osmnx + networkx +
Geofabrik PBF, chạy offline).

## Snap

Mỗi điểm user click được snap về node gần nhất trong graph theo
quy trình 2 bước (`application/snap_service.py`):

1. **Bbox check**: point phải nằm trong `metadata.bbox`. Ngoài → raise
   `AcceptedAreaError` → HTTP 422.
2. **Nearest + 200m**: lấy node gần nhất qua `GridSpatialIndex` (16×16
   cell bucket + ring search). Nếu Haversine(point, node) >
   `max_snap_distance_meters` (200m) → raise `AcceptedAreaError`.

## CostMatrix (many-to-many)

`CostMatrix(runtime, options)` ở `application/cost_matrix.py` tiền-tính
khoảng cách giữa mọi cặp node trong danh sách (vd shippers + pickups +
dropoffs). Cache reuse `RouteCache` (LRU 1000, key =
`(graph_version, options_hash, src_node, dst_node)`).

API: `get_distance(src, dst) -> float | None`, `get_path(src, dst) ->
list[str] | None`, `compute_for_nodes(node_ids)`.

Khi cache miss: chạy Bidirectional Dijkstra, lưu cache, store entry. Khi
disconnected: store entry với `distance_meters = inf`, `path_node_ids = []`.

## Reconstruct

`reconstruct_route_points` build:

```text
route_points = [clicked_start, ...graph_nodes, clicked_end]
```

Sau đó dedupe adjacent exact coordinate (tolerance 1e-9) để tránh vẽ
đoạn zero-length ở endpoint khi user click trùng node.

Distance tổng:

```text
distance = start_snap_distance + graph_distance + end_snap_distance
```

Áp dụng thống nhất cho cả `/route`, `/assignments` (mỗi leg =
shipper→pickup, pickup→dropoff), `/tours` và `/fleet` (mỗi leg =
current→next_stop).

## Assignment (1 đơn + N shipper)

`rank_shippers_for_order` ở `domain/assignment.py`: cho mỗi shipper, tính
tổng quãng đường `leg to_pickup` + `leg to_dropoff` qua `CostMatrix`,
sort tăng dần, `feasible=true` nếu cả 2 leg finite. Trả
`recommended_shipper_id` = shipper feasible rank 1.

## TSP (1 shipper + N đơn)

`optimize_tour` ở `domain/tsp.py`:

- ≤ 8 stops: **brute-force** thử mọi permutation thỏa precedence
  (pickup trước dropoff) → trả `optimal=True`.
- > 8 stops: **nearest-neighbor heuristic** + **2-opt local search** (giữ
  precedence) → trả `optimal=False`.

Distance giữa 2 stop lấy từ `CostMatrix.get_distance` (precomputed).

## VRP (M shipper + N đơn)

`solve_vrp` ở `domain/vrp.py`:

- ≤ 3 đơn + ≤ 2 shipper: **brute-force** thử mọi `product(shipper_ids,
  repeat=len(orders))` assignment, mỗi shipper con tour dùng `optimize_tour`
  (brute-force tiếp) → trả `optimal=True`.
- Lớn hơn: **cheapest-insertion** (cho từng đơn tìm shipper + vị trí
  insert tăng cost ít nhất) + **intra 2-opt** (từng tour) + **inter
  relocate** (move order từ shipper này sang shipper khác nếu tổng
  giảm) → trả `optimal=False`.

Đơn disconnects / inf cost được đưa vào `unassigned_order_ids`.
