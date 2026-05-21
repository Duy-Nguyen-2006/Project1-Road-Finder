# Frontend Walkthrough Checklist

This checklist tracks the frontend implementation order for the Road Finder app.

Read this file when working on frontend details. For the full frontend design, read `frontend/Frontend_Structure.md` first.

## Current frontend status

Frontend first MVP app is built.

The frontend can now:

- run as a React + Vite app
- show an OpenStreetMap map with Leaflet
- let the user choose point selection mode: Start A, End B, or Waypoint
- let the user click the map to set Start A
- let the user click the map to set End B
- let the user click the map to add waypoint points
- show selected points as markers with role colors
- show Start A, End B, and waypoints in a list
- remove selected points
- clear all selected points
- prepare route points in `[start, ...waypoints, end]` order for `POST /optimize-route`
- draw a returned route polyline when backend returns `ordered_points`

Important note: the backend is still a stub, so the current returned route order is not truly optimized yet.

## Before frontend coding

- [x] Understand project goal from `plans/Plan.md`
- [x] Understand backend API from `backend/app/routers/route_api.py`
- [x] Understand backend request and response models from `backend/app/models/route_models.py`
- [x] Create `frontend/Frontend_Structure.md`
- [x] Create `frontend/Walkthrough.md`

## Frontend first version

- [x] Create React + Vite app shell
  - [x] Create `frontend/package.json`
  - [x] Create `frontend/index.html`
  - [ ] Create `frontend/vite.config.js`
  - [x] Create `frontend/src/main.jsx`
  - [x] Create `frontend/src/App.jsx`
  - [x] Create `frontend/src/App.css`

- [x] Install frontend dependencies
  - [x] Add `react`
  - [x] Add `react-dom`
  - [x] Add `vite`
  - [x] Add `@vitejs/plugin-react`
  - [x] Add `leaflet`
  - [x] Add `react-leaflet`
  - [x] Add `@tanstack/react-query`

- [x] Create frontend point conversion helpers
  - [x] Create `frontend/src/types/point.js`
  - [x] Define `toBackendPoint(leafletPoint)`
  - [x] Define `toLeafletPoint(apiPoint)`
  - [x] Confirm backend fields are `latitude` and `longitude`
  - [x] Confirm Leaflet fields are `lat` and `lng`

- [x] Create backend API client
  - [x] Create `frontend/src/api/routeApi.js`
  - [x] Define `API_BASE_URL`
  - [x] Define `checkHealth()` for `GET /health`
  - [x] Define `optimizeRoute(points)` for `POST /optimize-route`
  - [x] Send request body as `{ points }`
  - [x] Read response body from `ordered_points`

- [x] Create route point state hook
  - [x] Create `frontend/src/hooks/useRoutePoints.js`
  - [x] Store `selectionMode`
  - [x] Store `startPoint`
  - [x] Store `endPoint`
  - [x] Store `waypoints`
  - [x] Store `selectedPoints`
  - [x] Store `orderedPoints`
  - [x] Define `addPoint(point)`
  - [x] Define `removePoint(role, index)`
  - [x] Define `clearPoints()`
  - [x] Define `setRouteResult(points)`

- [x] Create map component
  - [x] Create `frontend/src/components/MapView.jsx`
  - [x] Render Leaflet map with OpenStreetMap tiles
  - [x] Add click handler for map point selection
  - [x] Support Start A, End B, and Waypoint roles
  - [x] Show selected points as markers
  - [x] Draw route polyline from `orderedPoints`
  - [x] Import or support Leaflet CSS
  - [x] Make sure map container has a visible height

- [x] Create route controls component
  - [x] Create `frontend/src/components/RouteControls.jsx`
  - [x] Add Start A selection mode button
  - [x] Add End B selection mode button
  - [x] Add Waypoint selection mode button
  - [x] Add Optimize Route button
  - [x] Add Clear button
  - [x] Disable Optimize Route until Start A and End B are selected
  - [x] Show loading state while route optimization is running

- [x] Create selected point list component
  - [x] Create `frontend/src/components/PointList.jsx`
  - [x] Show Start A
  - [x] Show End B
  - [x] Show waypoint points
  - [x] Show latitude and longitude values
  - [x] Add remove button for each point

- [x] Wire frontend app together
  - [x] Use `useRoutePoints()` in `frontend/src/App.jsx`
  - [x] Render `MapView`
  - [x] Render `RouteControls`
  - [x] Render `PointList`
  - [x] Use TanStack Query mutation for route optimization
  - [x] Convert selected points before sending to backend
  - [x] Convert returned ordered points before drawing on map
  - [x] Show basic error message if backend request fails

## Frontend local testing

- [ ] Start backend server
  - [ ] Run FastAPI with Uvicorn from `backend/`
  - [ ] Confirm `GET /health` returns `{ "status": "ok" }`

- [x] Start frontend dev server
  - [x] Run frontend install command
  - [x] Run Vite dev server
  - [x] Open frontend in browser

- [x] Test map flow
  - [x] Map loads correctly
  - [x] User can choose Start A mode and set A on the map
  - [x] User can choose End B mode and set B on the map
  - [x] User can choose Waypoint mode and add waypoint points
  - [x] Markers appear for selected points
  - [x] Selected points appear in point list
  - [x] User can remove one selected point
  - [x] User can clear all selected points

- [ ] Test backend connection
  - [ ] Select Start A and End B
  - [ ] Optionally select waypoint points
  - [ ] Click Optimize Route
  - [ ] Frontend sends `POST /optimize-route`
  - [ ] Backend returns `ordered_points`
  - [ ] Frontend draws route polyline

## Later frontend version

- [ ] Add environment config
  - [ ] Use `VITE_API_BASE_URL`
  - [ ] Document `.env` example

- [ ] Improve map UI
  - [ ] Add different marker style for first point
  - [ ] Add different marker style for last point
  - [ ] Add route distance display when backend supports distance
  - [ ] Add point numbering on markers

- [ ] Improve user experience
  - [ ] Add loading spinner
  - [ ] Add better error messages
  - [ ] Add empty state text
  - [ ] Add responsive mobile layout

- [ ] Support real optimized route results
  - [ ] Confirm frontend works when backend returns reordered points
  - [ ] Draw route using returned order only
  - [ ] Do not assume returned order matches selected order

## API data reminder

Frontend selected route state should be ordered as Start A, waypoints, then End B before sending to backend.

Frontend map point state should look like this:

```js
[
  { lat: 10.762622, lng: 106.660172 },
  { lat: 10.776889, lng: 106.700806 }
]
```

Frontend request to backend should look like this:

```json
{
  "points": [
    { "latitude": 10.762622, "longitude": 106.660172 },
    { "latitude": 10.776889, "longitude": 106.700806 }
  ]
}
```

Backend response to frontend should look like this:

```json
{
  "ordered_points": [
    { "latitude": 10.762622, "longitude": 106.660172 },
    { "latitude": 10.776889, "longitude": 106.700806 }
  ]
}
```

Frontend route drawing data should look like this:

```js
[
  { lat: 10.762622, lng: 106.660172 },
  { lat: 10.776889, lng: 106.700806 }
]
```

## Next step

The next best frontend step is to run the backend server, test `POST /optimize-route` from the Start A / End B frontend flow, and confirm the returned `ordered_points` draw a route polyline on the map.
