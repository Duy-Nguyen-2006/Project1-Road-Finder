import React, { useCallback, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import MapView from "./components/MapView";
import ModeSwitcher from "./components/ModeSwitcher";
import OptionsPanel from "./components/OptionsPanel";
import FleetResultPanel from "./components/FleetResultPanel";
import PointList from "./components/PointList";
import {
  ACCEPTED_AREA_DETAIL,
  getGraphBounds,
  postFleet,
} from "./api/routeApi";
import { isInsideBbox } from "./utils/geo";
import { formatDistance } from "./utils/format";
import {
  PLACEMENT_MODE,
  ORDER_STEP,
  VRP_STATUS,
  useVrpState,
  getShipperColor,
} from "./hooks/useVrpState";

export default function App() {
  const {
    placementMode,
    setPlacementMode,
    orderStep,
    orders,
    shippers,
    pendingPickup,
    fleetResult,
    status,
    errorMessage,
    avoidRoadTypes,
    setAvoidRoadTypes,
    canOptimize,
    addPickup,
    addDropoff,
    addShipper,
    removeOrder,
    removeShipper,
    clearAll,
    beginRequest,
    completeRequest,
    failRequest,
  } = useVrpState();

  const boundsQuery = useQuery({
    queryKey: ["graph-bounds"],
    queryFn: getGraphBounds,
    staleTime: Infinity,
    retry: 1,
  });

  const boundsLoaded = boundsQuery.isSuccess && Boolean(boundsQuery.data?.bbox);
  const bbox = boundsLoaded ? boundsQuery.data.bbox : null;

  const mutation = useMutation({
    mutationFn: postFleet,
    onMutate: () => {
      beginRequest();
    },
    onSuccess: (data) => {
      completeRequest(data);
    },
    onError: (error) => {
      failRequest(error?.message || "Có lỗi xảy ra khi tối ưu.");
    },
  });

  const handleMapClick = useCallback(
    (rawPoint) => {
      if (!boundsLoaded) return;
      const candidate = {
        latitude: rawPoint.lat,
        longitude: rawPoint.lng,
      };
      if (!isInsideBbox(candidate, bbox)) {
        failRequest(ACCEPTED_AREA_DETAIL);
        return;
      }

      if (placementMode === PLACEMENT_MODE.ORDER) {
        if (orderStep === ORDER_STEP.PICKUP) {
          addPickup(candidate);
        } else {
          addDropoff(candidate);
        }
      } else {
        addShipper(candidate);
      }
    },
    [boundsLoaded, bbox, placementMode, orderStep, addPickup, addDropoff, addShipper, failRequest]
  );

  const handleOptimize = useCallback(() => {
    if (!canOptimize) return;
    mutation.mutate({
      shippers: shippers.map((s) => ({
        id: s.id,
        location: s.location,
      })),
      orders: orders.map((o) => ({
        id: o.id,
        pickup: o.pickup,
        dropoff: o.dropoff,
      })),
      options: {
        avoid_road_types: avoidRoadTypes,
        avoid_edge_ids: [],
      },
    });
  }, [canOptimize, mutation, shippers, orders, avoidRoadTypes]);

  const statusText = useMemo(() => {
    if (!boundsLoaded) return "Đang tải vùng hỗ trợ...";
    if (status === VRP_STATUS.LOADING) return "Đang tối ưu...";
    if (status === VRP_STATUS.ERROR) return errorMessage;
    if (status === VRP_STATUS.SUCCESS && fleetResult) {
      return `Tổng quãng đường đội: ${formatDistance(fleetResult.total_distance_meters)}`;
    }
    return "Chọn đơn hàng và shipper, sau đó bấm \"Tối ưu đội\".";
  }, [boundsLoaded, status, errorMessage, fleetResult]);

  // Shipper color mapping
  const shipperColorMap = useMemo(() => {
    const map = {};
    shippers.forEach((s, i) => {
      map[s.id] = getShipperColor(i);
    });
    return map;
  }, [shippers]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>VRP Delivery Routing</h1>
        <p>Tối ưu giao vận đa-shipper. Chọn đơn hàng và shipper trên bản đồ.</p>
      </header>

      <main className="app-content">
        <section className="map-panel">
          <MapView
            bounds={bbox}
            orders={orders}
            shippers={shippers}
            pendingPickup={pendingPickup}
            fleetResult={fleetResult}
            shipperColorMap={shipperColorMap}
            selectionEnabled={boundsLoaded}
            onAddPoint={handleMapClick}
            placementMode={placementMode}
          />
        </section>

        <aside className="side-panel">
          <ModeSwitcher
            placementMode={placementMode}
            onPlacementModeChange={setPlacementMode}
            orderStep={orderStep}
          />

          <OptionsPanel
            avoidRoadTypes={avoidRoadTypes}
            onAvoidRoadTypesChange={setAvoidRoadTypes}
          />

          <div className="panel-card controls-card">
            <button
              className="primary-button"
              onClick={handleOptimize}
              disabled={!canOptimize}
              type="button"
            >
              {status === VRP_STATUS.LOADING ? "Đang tối ưu..." : "Tối ưu đội"}
            </button>
            <button
              className="secondary-button"
              onClick={clearAll}
              disabled={orders.length === 0 && shippers.length === 0}
              type="button"
            >
              Xóa tất cả
            </button>
          </div>

          <PointList
            orders={orders}
            shippers={shippers}
            shipperColorMap={shipperColorMap}
            onRemoveOrder={removeOrder}
            onRemoveShipper={removeShipper}
          />

          {status === VRP_STATUS.SUCCESS && fleetResult ? (
            <FleetResultPanel
              fleetResult={fleetResult}
              shipperColorMap={shipperColorMap}
            />
          ) : (
            <div className="panel-card">
              <h2>Trạng thái</h2>
              <p
                className={
                  status === VRP_STATUS.ERROR ? "error-text" : "helper-text"
                }
              >
                {statusText}
              </p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
