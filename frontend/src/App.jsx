import React from "react";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import MapView from "./components/MapView";
import PointList from "./components/PointList";
import RouteControls from "./components/RouteControls";
import { optimizeRoute } from "./api/routeApi";
import { toBackendPoint, toLeafletPoint } from "./types/point";
import { useRoutePoints } from "./hooks/useRoutePoints";

export default function App() {
  const {
    selectionMode,
    setSelectionMode,
    startPoint,
    endPoint,
    waypoints,
    selectedPoints,
    orderedPoints,
    addPoint,
    removePoint,
    clearPoints,
    setRouteResult,
  } = useRoutePoints();
  const [errorMessage, setErrorMessage] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = selectedPoints.map(toBackendPoint);
      const result = await optimizeRoute(payload);
      return result;
    },
    onSuccess: (data) => {
      const routePoints = (data.ordered_points || []).map(toLeafletPoint);
      setRouteResult(routePoints);
      setErrorMessage("");
    },
    onError: (error) => {
      setErrorMessage(error.message || "Có lỗi xảy ra khi gọi backend.");
    },
  });

  const handleOptimize = () => {
    if (!startPoint || !endPoint) {
      setErrorMessage("Cần chọn đủ Start A và End B trước khi tối ưu route.");
      return;
    }
    mutation.mutate();
  };

  const routePreviewCount = useMemo(() => orderedPoints.length, [orderedPoints]);
  const waypointCount = waypoints.length;

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Road Finder</h1>
        <p>Chọn điểm A, điểm B và waypoint trung gian để tìm lộ trình.</p>
      </header>

      <main className="app-content">
        <section className="map-panel">
          <MapView selectedPoints={selectedPoints} orderedPoints={orderedPoints} onAddPoint={addPoint} />
        </section>

        <aside className="side-panel">
          <RouteControls
            selectionMode={selectionMode}
            onSelectionModeChange={setSelectionMode}
            startPoint={startPoint}
            endPoint={endPoint}
            selectedPoints={selectedPoints}
            onOptimize={handleOptimize}
            onClear={clearPoints}
            isOptimizing={mutation.isPending}
          />

          <PointList startPoint={startPoint} endPoint={endPoint} waypoints={waypoints} onRemovePoint={removePoint} />

          <div className="panel-card">
            <h2>Kết quả</h2>
            <p>Số điểm route hiện tại: {routePreviewCount}</p>
            <p>Số waypoint trung gian: {waypointCount}</p>
            {errorMessage ? <p className="error-text">{errorMessage}</p> : <p className="helper-text">Sẵn sàng nhận dữ liệu từ backend.</p>}
          </div>
        </aside>
      </main>
    </div>
  );
}
