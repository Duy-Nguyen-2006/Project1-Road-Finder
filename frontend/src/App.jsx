import React, { useCallback, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import MapView from "./components/MapView";
import PointList from "./components/PointList";
import RouteControls from "./components/RouteControls";
import { findShortestPath, getGraphBounds } from "./api/routeApi";
import { isInsideBbox } from "./utils/geo";
import { formatDistance } from "./utils/format";
import {
  ROUTE_STATUS,
  SELECTION_MODES,
  useRoutePoints,
} from "./hooks/useRoutePoints";

const ACCEPTED_AREA_MESSAGE = "Error: Not in accepted area";

export default function App() {
  const queryClient = useQueryClient();
  const {
    selectionMode,
    setSelectionMode,
    startPoint,
    endPoint,
    route,
    status,
    errorMessage,
    bounds,
    canFindRoute,
    addPoint,
    removePoint,
    clearAll,
    beginRouteRequest,
    completeRouteRequest,
    failRouteRequest,
  } = useRoutePoints({ bounds: null });

  const boundsQuery = useQuery({
    queryKey: ["graph-bounds"],
    queryFn: getGraphBounds,
    staleTime: Infinity,
    retry: 1,
  });

  const boundsLoaded = boundsQuery.isSuccess && Boolean(boundsQuery.data?.bbox);
  const boundsError =
    boundsQuery.isError && boundsQuery.error
      ? boundsQuery.error.message
      : "";
  const bbox = boundsLoaded ? boundsQuery.data.bbox : null;

  const mutation = useMutation({
    mutationFn: findShortestPath,
    onMutate: () => {
      beginRouteRequest();
    },
    onSuccess: (data) => {
      completeRouteRequest(data);
    },
    onError: (error) => {
      failRouteRequest(error?.message || "Có lỗi xảy ra khi tìm đường.");
    },
  });

  const handleAddPoint = useCallback(
    (rawPoint) => {
      if (!boundsLoaded) return;
      const candidate = {
        latitude: rawPoint.lat,
        longitude: rawPoint.lng,
      };
      if (!isInsideBbox(candidate, bbox)) {
        failRouteRequest(ACCEPTED_AREA_MESSAGE);
        return;
      }
      addPoint(candidate);
    },
    [addPoint, bbox, boundsLoaded, failRouteRequest]
  );

  const handleFindRoute = useCallback(() => {
    if (!startPoint || !endPoint) return;
    mutation.mutate({
      start: { latitude: startPoint.latitude, longitude: startPoint.longitude },
      end: { latitude: endPoint.latitude, longitude: endPoint.longitude },
    });
  }, [endPoint, mutation, startPoint]);

  const handleClear = useCallback(() => {
    clearAll();
  }, [clearAll]);

  const handleRemovePoint = useCallback(
    (role) => {
      removePoint(role);
    },
    [removePoint]
  );

  const selectionEnabled = boundsLoaded;

  const distanceText = useMemo(
    () => (route && typeof route.distance === "number" ? formatDistance(route.distance) : null),
    [route]
  );

  const statusText = useMemo(() => {
    if (!boundsLoaded) return "Đang tải vùng hỗ trợ từ backend...";
    if (status === ROUTE_STATUS.LOADING) return "Đang tìm đường...";
    if (status === ROUTE_STATUS.SUCCESS && distanceText) {
      return `Đã tìm được đường đi (${distanceText}).`;
    }
    if (status === ROUTE_STATUS.ERROR) return errorMessage;
    if (boundsError) return `Lỗi tải vùng hỗ trợ: ${boundsError}`;
    return "Chọn Start và End trong vùng bbox đỏ, sau đó bấm Find Shortest Path.";
  }, [boundsError, boundsLoaded, distanceText, errorMessage, status]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Road Finder</h1>
        <p>Chọn Start và End trong vùng bbox đỏ của TP.HCM, bấm Find Shortest Path.</p>
      </header>

      <main className="app-content">
        <section className="map-panel">
          <MapView
            bounds={bbox}
            startPoint={startPoint}
            endPoint={endPoint}
            routePoints={route?.route_points}
            selectionEnabled={selectionEnabled}
            onAddPoint={handleAddPoint}
          />
        </section>

        <aside className="side-panel">
          <RouteControls
            selectionMode={selectionMode}
            onSelectionModeChange={setSelectionMode}
            startPoint={startPoint}
            endPoint={endPoint}
            status={status}
            boundsLoaded={boundsLoaded}
            onFindRoute={handleFindRoute}
            onClear={handleClear}
          />

          <PointList
            startPoint={startPoint}
            endPoint={endPoint}
            onRemovePoint={handleRemovePoint}
          />

          <div className="panel-card">
            <h2>Kết quả</h2>
            {status === ROUTE_STATUS.SUCCESS && route ? (
              <>
                <p>
                  <strong>Quãng đường:</strong> {distanceText}
                </p>
                <p className="helper-text">
                  Từ node {route.start_node_id} đến node {route.end_node_id}.
                </p>
              </>
            ) : (
              <p
                className={
                  status === ROUTE_STATUS.ERROR || boundsError
                    ? "error-text"
                    : "helper-text"
                }
              >
                {statusText}
              </p>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}
