# Project Walkthrough

This file tracks the big changes needed for the whole Road Finder project.

## How to read this project

For a newbie, read files in this order:

1. `plans/Plan.md`
   - Understand the goal, tech stack, system flow, and build order.

2. `Walkthrough.md`
   - See the big project checklist and know what to do next.

3. `backend/Backend-Structure.md`
   - Read this when working on backend details.

4. `backend/Walkthrough.md`
   - Follow this when checking backend progress.

5. Backend source code:
   - `backend/app/models/point.py`
   - `backend/app/models/route_models.py`
   - `backend/app/services/tsp_service.py`
   - `backend/app/routers/route_api.py`
   - `backend/app/main.py`

## Working process rule

Before changing code or documents, always do this:

1. Read `Walkthrough.md` first.
   - Understand the current project status.
   - Check the next big step.

2. If working on backend, also read `backend/Walkthrough.md`.
   - Understand the backend-specific progress.
   - Check which backend tasks are done and which are still pending.

3. Make the code or document change.

4. After the change, update the related walkthrough file.
   - Update `Walkthrough.md` for project-level progress.
   - Update `backend/Walkthrough.md` for backend-specific progress.

5. Only mark a checkbox as done when the work is actually complete.

6. Before pushing to Git, check that walkthrough files match the real project state.

This keeps the project easy for a newbie to follow.

## Current status

Backend first version is complete.

Frontend MVP first version is also partially complete. The frontend can now run as a React + Vite app, show a Leaflet/OpenStreetMap map, let the user define Start A, End B, and waypoint points, and show selected points as markers/list items.

The backend can now:

- define map points
- receive route optimization request data
- return route optimization response data
- expose `GET /health`
- expose `POST /optimize-route`
- run as a FastAPI app

Important note: the backend does not optimize with OR-Tools yet. The current route service is still a stub and returns the same points.

## Big project changes

- [x] Create project folders
  - [x] Create `backend/`
  - [x] Create `frontend/`
  - [x] Create `plans/`

- [x] Build backend API first version
  - [x] Create `backend/app/models/point.py`
  - [x] Create `backend/app/models/route_models.py`
  - [x] Create `backend/app/services/tsp_service.py`
  - [x] Create `backend/app/routers/route_api.py`
  - [x] Create `backend/app/main.py`
  - [x] Create `backend/requirements.txt`

- [ ] Test backend API locally
  - [ ] Install backend dependencies
  - [ ] Run FastAPI with Uvicorn
  - [ ] Test `GET /health`
  - [ ] Test `POST /optimize-route`

- [x] Build frontend app
  - [x] Create React + Vite project
  - [x] Add Leaflet map
  - [x] Let user define Start A and End B on the map
  - [x] Let user add waypoint points on the map
  - [x] Show selected points as markers

- [ ] Connect frontend and backend
  - [ ] Send selected points to `POST /optimize-route`
  - [ ] Receive ordered points from backend
  - [ ] Draw the returned route on the map

- [ ] Add real route optimization
  - [ ] Add distance calculation
  - [ ] Add distance matrix builder
  - [ ] Add OR-Tools TSP solver
  - [ ] Return optimized ordered points

- [ ] Final cleanup
  - [ ] Add README instructions
  - [ ] Test backend API
  - [ ] Test frontend map flow
  - [ ] Verify full route optimization flow

## Next step

The next best step is to run the backend API locally and test the full frontend-to-backend route flow: define Start A and End B on the map, optionally add waypoint points, click `Optimize Route`, receive `ordered_points`, and draw the route polyline.
