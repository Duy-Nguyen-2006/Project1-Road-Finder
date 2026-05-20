# Backend Walkthrough Checklist

This checklist tracks the backend implementation order for the Road Finder app.

## Backend first version

- [x] Create `backend/app/models/point.py`
  - [x] Define `Point`
  - [x] Add `latitude`
  - [x] Add `longitude`
  - [x] Add example data comment

- [x] Create `backend/app/models/route.py`
  - [x] Define `OptimizeRouteRequest`
  - [x] Define `OptimizeRouteResponse`
  - [x] Use `Point` for request and response data

- [x] Create `backend/app/services/tsp_service.py`
  - [x] Define `optimize_points(points)`
  - [x] Return the same points first as a stub

- [x] Create `backend/app/routers/route.py`
  - [x] Create `router = APIRouter()`
  - [x] Add `GET /health`
  - [x] Add `POST /optimize-route`
  - [x] Call `optimize_points(payload.points)`

- [x] Create `backend/app/main.py`
  - [x] Define `create_app()`
  - [x] Create the `FastAPI` app
  - [x] Include the route router
  - [x] Expose `app = create_app()`

- [x] Create `backend/requirements.txt`
  - [x] Add `fastapi`
  - [x] Add `uvicorn[standard]`
  - [x] Add `pydantic`

## Later backend version

- [ ] Create `backend/app/utils/distance.py`
  - [ ] Define `haversine_distance(a, b)`

- [ ] Improve `backend/app/services/tsp_service.py`
  - [ ] Define `build_distance_matrix(points)`
  - [ ] Define `solve_tsp(distance_matrix)`
  - [ ] Add OR-Tools route optimization

- [ ] Update `backend/requirements.txt`
  - [ ] Add `ortools`
