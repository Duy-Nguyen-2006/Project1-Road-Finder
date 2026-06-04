# API Contracts

## GET /health

Returns `{"status": "ok"}`.

## POST /shortest-path

Request:
```json
{
  "start": {"latitude": 10.1, "longitude": 106.1},
  "end": {"latitude": 10.2, "longitude": 106.2}
}
```

Response:
```json
{
  "route_points": [...],
  "distance": 1200,
  "start_node_id": "A",
  "end_node_id": "B"
}
```
