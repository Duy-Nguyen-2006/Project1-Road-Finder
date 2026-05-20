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

- [ ] Create `backend/app/services/tsp_service.py`
  - [ ] Define `optimize_points(points)`
  - [ ] Return the same points first as a stub

- [ ] Create `backend/app/routers/route.py`
  - [ ] Create `router = APIRouter()`
  - [ ] Add `GET /health`
  - [ ] Add `POST /optimize-route`
  - [ ] Call `optimize_points(payload.points)`

- [ ] Create `backend/app/main.py`
  - [ ] Define `create_app()`
  - [ ] Create the `FastAPI` app
  - [ ] Include the route router
  - [ ] Expose `app = create_app()`

- [ ] Create `backend/requirements.txt`
  - [ ] Add `fastapi`
  - [ ] Add `uvicorn[standard]`
  - [ ] Add `pydantic`

## Later backend version

- [ ] Create `backend/app/utils/distance.py`
  - [ ] Define `haversine_distance(a, b)`

- [ ] Improve `backend/app/services/tsp_service.py`
  - [ ] Define `build_distance_matrix(points)`
  - [ ] Define `solve_tsp(distance_matrix)`
  - [ ] Add OR-Tools route optimization

- [ ] Update `backend/requirements.txt`
  - [ ] Add `ortools`
