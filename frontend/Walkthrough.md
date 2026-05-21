# Frontend Walkthrough Checklist

This checklist tracks the frontend implementation order for the Road Finder app.

Read this file when working on frontend details. For the full frontend design, read `frontend/Frontend_Structure.md` first.

## Current frontend status

Frontend planning documents are created.

The actual React + Vite frontend app has not been built yet.

## Before frontend coding

- [x] Understand project goal from `plans/Plan.md`
- [x] Understand backend API from `backend/app/routers/route_api.py`
- [x] Understand backend request and response models from `backend/app/models/route_models.py`
- [x] Create `frontend/Frontend_Structure.md`
- [x] Create `frontend/Walkthrough.md`

## Frontend first version

- [ ] Create React + Vite app shell
  - [ ] Create `frontend/package.json`
  - [ ] Create `frontend/index.html`
  - [ ] Create `frontend/vite.config.js`
  - [ ] Create `frontend/src/main.jsx`
  - [ ] Create `frontend/src/App.jsx`
  - [ ] Create `frontend/src/App.css`

- [ ] Install frontend dependencies
  - [ ] Add `react`
  - [ ] Add `react-dom`
  - [ ] Add `vite`
  - [ ] Add `@vitejs/plugin-react`
  - [ ] Add `leaflet`
  - [ ] Add `react-leaflet`
  - [ ] Add `@tanstack/react-query`

- [ ] Create frontend point conversion helpers
  - [ ] Create `frontend/src/types/point.js`
  - [ ] Define `toBackendPoint(leafletPoint)`
  - [ ] Define `toLeafletPoint(apiPoint)`
  - [ ] Confirm backend fields are `latitude` and `longitude`
  - [ ] Confirm Leaflet fields are `lat` and `lng`

- [ ] Create backend API client
  - [ ] Create `frontend/src/api/routeApi.js`
  - [ ] Define `API_BASE_URL`
  - [ ] Define `checkHealth()` for `GET /health`
  - [ ] Define `optimizeRoute(points)` for `POST /optimize-route`
  - [ ] Send request body as `{ points }`
  - [ ] Read response body from `ordered_points`

- [ ] Create route point state hook
  - [ ] Create `frontend/src/hooks/useRoutePoints.js`
  - [ ] Store `selectedPoints`
  - [ ] Store `orderedPoints`
  - [ ] Define `addPoint(point)`
  - [ ] Define `removePoint(index)`
  - [ ] Define `clearPoints()`
  - [ ] Define `setRouteResult(points)`

- [ ] Create map component
  - [ ] Create `frontend/src/components/MapView.jsx`
  - [ ] Render Leaflet map with OpenStreetMap tiles
  - [ ] Add click handler for map point selection
  - [ ] Show selected points as markers
  - [ ] Draw route polyline from `orderedPoints`
  - [ ] Import or support Leaflet CSS
  - [ ] Make sure map container has a visible height

- [ ] Create route controls component
  - [ ] Create `frontend/src/components/RouteControls.jsx`
  - [ ] Add Optimize Route button
  - [ ] Add Clear button
  - [ ] Disable Optimize Route when fewer than two points are selected
  - [ ] Show loading state while route optimization is running

- [ ] Create selected point list component
  - [ ] Create `frontend/src/components/PointList.jsx`
  - [ ] Show selected points
  - [ ] Show latitude and longitude values
  - [ ] Add remove button for each point

- [ ] Wire frontend app together
  - [ ] Use `useRoutePoints()` in `frontend/src/App.jsx`
  - [ ] Render `MapView`
  - [ ] Render `RouteControls`
  - [ ] Render `PointList`
  - [ ] Use TanStack Query mutation for route optimization
  - [ ] Convert selected points before sending to backend
  - [ ] Convert returned ordered points before drawing on map
  - [ ] Show basic error message if backend request fails

## Frontend local testing

- [ ] Start backend server
  - [ ] Run FastAPI with Uvicorn from `backend/`
  - [ ] Confirm `GET /health` returns `{ "status": "ok" }`

- [ ] Start frontend dev server
  - [ ] Run frontend install command
  - [ ] Run Vite dev server
  - [ ] Open frontend in browser

- [ ] Test map flow
  - [ ] Map loads correctly
  - [ ] User can click map to add points
  - [ ] Markers appear for selected points
  - [ ] Selected points appear in point list
  - [ ] User can remove one selected point
  - [ ] User can clear all selected points

- [ ] Test backend connection
  - [ ] Select at least two points
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

Frontend map state should look like this:

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

The next best frontend step is to create the React + Vite app shell in `frontend/`, then add Leaflet map point selection.
