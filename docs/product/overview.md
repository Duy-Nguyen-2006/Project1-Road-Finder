# Product Overview

Road Finder is a web app that lets a user choose a Start point and an End point on a map, then asks the backend to find the shortest path between them on a road graph.

## Vision

Help a user visually select two locations and see the shortest available road route between them.

## Primary Flow

1. User opens the web app.
2. User selects a Start point on the map.
3. User selects an End point on the map.
4. User clicks **Find Shortest Path**.
5. Backend finds the shortest path using Dijkstra.
6. Frontend draws the resulting route on the map.
7. Frontend displays useful route metadata such as total distance.

## Out of Scope (First Version)

- Waypoint ordering / TSP
- Turn-by-turn navigation
- Live traffic
- User accounts
- Saved routes
- Mobile-native behavior

## Stack

- Backend: FastAPI (Python)
- Frontend: React + Vite + Leaflet
- Data: Local OSM-derived graph JSON

## Related Docs

- `routing.md` — Algorithm and graph details
- `api.md` — HTTP contracts
- `frontend-flow.md` — UI interactions
