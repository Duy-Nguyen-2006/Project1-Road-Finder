# Frontend Flow

UI tiếng Việt primary. State + dispatch tập trung ở `useVrpState` hook.
TanStack Query lo fetch/cache bounds, `useMutation` lo gọi `/fleet`.

## Component Tree

```text
App.jsx
├── MapView.jsx              # Leaflet map (tiles + bbox rectangle + markers + polylines)
├── ModeSwitcher.jsx         # Order (Pickup/Dropoff) ↔ Shipper
├── OptionsPanel.jsx         # avoid_road_types multi-select
├── controls-card            # primary button "Tối ưu đội" + secondary "Xóa tất cả"
├── PointList.jsx            # orders + shippers list, có remove
├── FleetResultPanel.jsx     # per-shipper tour + unassigned
└── status-card              # status + error message
```

State tập trung ở `hooks/useVrpState.js` (custom hook). `App.jsx` wire
state → props cho từng component.

## State Shape

```text
{
  placementMode: 'order' | 'shipper',
  orderStep: 'pickup' | 'dropoff',
  orders: [
    { id: 'o1', pickup: Point, dropoff: Point }, ...
  ],
  shippers: [
    { id: 's1', location: Point }, ...
  ],
  pendingPickup: Point | null,        // pickup vừa click, chờ dropoff
  fleetResult: FleetResponse | null,
  status: 'idle' | 'loading' | 'success' | 'error',
  errorMessage: string,
  avoidRoadTypes: string[],           // vd ['highway', 'residential']
}
```

ID generation dùng module-level counter (`_nextOrderId`, `_nextShipperId`)
— đơn giản, không cần persist qua refresh.

## User Interactions

### 1. App load

- `useQuery({ queryKey: ['graph-bounds'], queryFn: getGraphBounds,
  staleTime: Infinity })` → disable click cho tới khi `isSuccess` +
  `data.bbox` truthy (`selectionEnabled = boundsLoaded`).
- Status text: "Đang tải vùng hỗ trợ..." khi `!boundsLoaded`.

### 2. Chọn đơn hàng (Order mode)

- `placementMode = 'order'`, `orderStep = 'pickup'` ban đầu.
- Click trong bbox (qua `MapClickHandler`):
  - Nếu `orderStep == 'pickup'`: `addPickup(point)` → set
    `pendingPickup = point`, tự chuyển `orderStep = 'dropoff'`. Map hiển
    thị marker màu vàng (PENDING_ICON).
  - Nếu `orderStep == 'dropoff'` (và `pendingPickup` tồn tại):
    `addDropoff(point)` → tạo `newOrder = { id, pickup: pendingPickup,
    dropoff: point }`, append vào `orders`, clear `pendingPickup`, reset
    `orderStep = 'pickup'`. `fleetResult = null`, `status = 'idle'`.
- Click ngoài bbox: `failRequest(ACCEPTED_AREA_DETAIL)` — set status=error
  với message "Error: Not in accepted area", **không** thay đổi
  `placementMode` / `orderStep` / `pendingPickup` / `orders` / `shippers`.
- Marker màu xanh lá (PICKUP_ICON) cho pickup, đỏ (DROPOFF_ICON) cho dropoff.

### 3. Chọn shipper (Shipper mode)

- `placementMode = 'shipper'`.
- Click trong bbox: `addShipper(point)` → append vào `shippers`, clear
  `fleetResult`, `status = 'idle'`.
- Click ngoài bbox: cùng `failRequest(ACCEPTED_AREA_DETAIL)`.
- Marker màu xanh dương (SHIPPER_ICON) cho mỗi shipper.

### 4. Routing options

`OptionsPanel` hiển thị checkboxes cho mỗi `road_type` thường gặp
(`highway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`).
Toggle set `avoidRoadTypes` trong state. State này gửi lên backend
trong `POST /fleet.options.avoid_road_types`.

### 5. Tối ưu đội

- Button "Tối ưu đội" disabled khi `!canOptimize` (orders rỗng HOẶC
  shippers rỗng HOẶC status=loading).
- Click → `mutation.mutate({ shippers, orders, options: { avoid_road_types,
  avoid_edge_ids: [] } })`.
- `onMutate`: `beginRequest()` → status=loading, clear errorMessage.
- `onSuccess`: `completeRequest(data)` → `fleetResult = data`, status=success.
- `onError`: `failRequest(error.message || 'Có lỗi xảy ra khi tối ưu.')`.
- Khi status=success: render `FleetResultPanel` thay cho status-card.
- Khi status=loading: button text đổi "Đang tối ưu...".

### 6. Xoá

- "Xóa tất cả" button (secondary): `clearAll()` → reset `orders`,
  `shippers`, `pendingPickup`, `orderStep`, `fleetResult`, `status`,
  `errorMessage`. Disabled khi cả `orders` và `shippers` rỗng.
- Trong `PointList`: mỗi order / shipper có nút "Xóa" riêng gọi
  `removeOrder` / `removeShipper` (clear `fleetResult` + status=idle).
- Trong `FleetResultPanel`: list "Đơn chưa gán" (`unassigned_order_ids`)
  hiển thị ID đơn để user biết cần xử lý thêm.

## Map Behaviors

- **Default center**: `[10.7769, 106.7009]` (Quận 1 TP.HCM), zoom 13.
- **bbox rectangle**: `<Rectangle bounds={rectangleBounds} pathOptions={{
  color: 'red', weight: 2, fillOpacity: 0.05 }} />` — fill mỏng để không
  che marker.
- **Fit bounds khi load**: `MapBoundsFitter` watch `bounds` → `map.fitBounds(latlngs, { padding: [24, 24] })`.
- **Fit bounds khi có result**: watch `tourPolylines` → `map.fitBounds(allPoints, { padding: [32, 32] })`. Trigger cả khi re-fit từ kết quả trước đó.
- **Invalidate size**: `MapInvalidator` chạy `setTimeout(() => map.invalidateSize(), 50)` sau mount (fix lỗi tile render trong flex layout).
- **Polylines**: 1 polyline mỗi shipper, màu theo `shipperColorMap` (palette
  8 màu, lặp theo index).

## Color Coding

| Element | Color | Icon constant |
| --- | --- | --- |
| Order pickup | green `#16a34a` | PICKUP_ICON |
| Order dropoff | red `#dc2626` | DROPOFF_ICON |
| Shipper (clicked) | blue `#2563eb` | SHIPPER_ICON |
| Pending pickup (chờ dropoff) | orange `#f59e0b` | PENDING_ICON |
| Bbox rectangle | red `red` | — |
| Tour polyline | per-shipper color | 8-color palette |

`SHIPPER_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c',
'#0891b2', '#ca8a04', '#e11d48']` (8 màu, lặp modulo).

## Error / Status Display

- Status-card (mặc định):
  - "Đang tải vùng hỗ trợ..." khi `!boundsLoaded`
  - "Đang tối ưu..." khi status=loading
  - `errorMessage` (class `error-text`) khi status=error
  - "Chọn đơn hàng và shipper, sau đó bấm \"Tối ưu đội\"." khi status=idle
- FleetResultPanel (khi status=success):
  - "Tổng quãng đường đội: {formatDistance(total_distance_meters)}"
  - Mỗi shipper: tên + color dot + `formatDistance(tour.total_distance_meters)` + list ordered_stops
  - Section "Đơn chưa gán" nếu `unassigned_order_ids.length > 0`
