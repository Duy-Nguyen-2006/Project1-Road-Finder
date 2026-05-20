# Project Walkthrough

This file tracks the big changes needed for the whole Road Finder project.

## Big project changes

- [x] Create project folders
  - [x] Create `backend/`
  - [x] Create `frontend/`
  - [x] Create `plans/`

- [ ] Build backend API
  - [x] Create `backend/app/models/point.py`
  - [ ] Create backend request and response models
  - [ ] Create backend route optimization service stub
  - [ ] Create backend API router
  - [ ] Create FastAPI app entry point
  - [ ] Add backend dependencies

- [ ] Build frontend app
  - [ ] Create React + Vite project
  - [ ] Add Leaflet map
  - [ ] Let user select points on the map
  - [ ] Show selected points as markers

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
