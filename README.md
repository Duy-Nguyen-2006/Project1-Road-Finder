# Road Finder

Road Finder là một web app giúp người dùng chọn các điểm trên bản đồ, gửi các điểm đó lên backend, tối ưu thứ tự đi qua các điểm và vẽ lại tuyến đường tối ưu trên bản đồ.

## Tính năng chính

- Hiển thị bản đồ bằng Leaflet và OpenStreetMap.
- Chọn điểm bắt đầu A, điểm kết thúc B và các waypoint trung gian.
- Gửi danh sách điểm từ frontend đến backend qua REST API.
- Backend snap điểm về giao lộ gần nhất từ OpenStreetMap nếu có dữ liệu giao lộ.
- Tối ưu thứ tự waypoint bằng thuật toán heuristic TSP: Nearest Neighbor + 2-opt.
- Lấy hình học tuyến đường thực tế từ OSRM public routing API.
- Vẽ tuyến đường trả về lên bản đồ frontend.

## Tech stack

### Frontend

- React 18
- Vite
- Leaflet
- React Leaflet
- TanStack Query
- Fetch API

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- Requests

### Dịch vụ bản đồ / định tuyến

- OpenStreetMap tiles
- Overpass API để lấy giao lộ
- OSRM public API để lấy route geometry

## Cấu trúc thư mục

```text
Project1-Road-Finder/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── models/                 # Pydantic request/response models
│   │   ├── routers/                # API routes
│   │   ├── services/               # Route optimization + OSM service
│   │   └── utils/                  # Distance utilities
│   ├── requirements.txt
│   └── Walkthrough.md
├── frontend/
│   ├── src/
│   │   ├── api/                    # Backend API client
│   │   ├── components/             # Map and route UI components
│   │   ├── hooks/                  # Route point state management
│   │   ├── types/                  # Point conversion helpers
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── plans/
│   └── Plan.md
└── Walkthrough.md
```

## Yêu cầu môi trường

- Python 3.10+
- Node.js 18+
- npm
- Internet connection để gọi Overpass API và OSRM API

## Cài đặt backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chạy backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend mặc định chạy tại:

```text
http://localhost:8000
```

## Cài đặt frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend mặc định chạy tại:

```text
http://localhost:5173
```

Nếu backend không chạy ở `http://localhost:8000`, tạo biến môi trường cho Vite:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## API endpoints

### `GET /health`

Kiểm tra backend đang chạy.

Response:

```json
{
  "status": "ok"
}
```

### `POST /optimize-route`

Nhận danh sách điểm và trả về danh sách điểm theo tuyến đường tối ưu.

Request:

```json
{
  "points": [
    { "latitude": 10.7769, "longitude": 106.7009 },
    { "latitude": 10.7829, "longitude": 106.6934 },
    { "latitude": 10.7715, "longitude": 106.6981 }
  ]
}
```

Response:

```json
{
  "ordered_points": [
    { "latitude": 10.7769, "longitude": 106.7009 },
    { "latitude": 10.7715, "longitude": 106.6981 },
    { "latitude": 10.7829, "longitude": 106.6934 }
  ]
}
```

### `GET /intersections`

Lấy danh sách giao lộ từ OpenStreetMap.

Query params:

- `city_name`: tên thành phố, mặc định là `Ho Chi Minh City`
- `bbox`: optional bounding box dạng `min_lat,min_lon,max_lat,max_lon`

Ví dụ:

```text
GET /intersections?city_name=Ho%20Chi%20Minh%20City
GET /intersections?bbox=10.70,106.60,10.85,106.80
```

## Luồng hoạt động

1. Người dùng mở frontend.
2. Người dùng chọn Start A, End B và waypoint trên bản đồ.
3. Frontend gửi danh sách điểm đến `POST /optimize-route`.
4. Backend lấy/cached giao lộ từ OSM nếu có.
5. Backend snap điểm người dùng về giao lộ gần nhất.
6. Backend tạo distance matrix bằng Haversine.
7. Backend tối ưu thứ tự đi qua điểm bằng Nearest Neighbor + 2-opt.
8. Backend gọi OSRM để lấy route geometry theo đường thật.
9. Frontend nhận `ordered_points` và vẽ polyline lên bản đồ.

## Kiểm thử nhanh

Kiểm tra backend health:

```bash
curl http://localhost:8000/health
```

Build frontend:

```bash
cd frontend
npm run build
```

## Ghi chú

- Lần gọi `/optimize-route` đầu tiên có thể chậm vì backend cần lấy và cache giao lộ từ Overpass API.
- Nếu OSRM API lỗi hoặc không có internet, backend fallback về danh sách điểm đã tối ưu thay vì route geometry chi tiết.
- Project hiện dùng heuristic TSP, chưa tích hợp OR-Tools.
