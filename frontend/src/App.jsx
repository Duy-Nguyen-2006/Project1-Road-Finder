import React, { useCallback, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import AuthPanel from "./components/AuthPanel";
import ScenarioPanel from "./components/ScenarioPanel";
import { useAuth } from "./hooks/useAuth";
import MapView from "./components/MapView";
import ModeSwitcher from "./components/ModeSwitcher";
import OptionsPanel from "./components/OptionsPanel";
import ShipperAssignmentPanel from "./components/ShipperAssignmentPanel";
import TourResultPanel from "./components/TourResultPanel";
import PointList from "./components/PointList";
import {
  ACCEPTED_AREA_DETAIL,
  getGraphBounds,
  postTours,
  API_BASE_URL,
} from "./api/routeApi";
import { isInsideBbox } from "./utils/geo";
import { formatDistance } from "./utils/format";
import { getOrderLabel } from "./utils/orders";
import { getShipperGlyph, getShipperLabel } from "./utils/shippers";
import {
  PLACEMENT_MODE,
  VRP_STATUS,
  useVrpState,
  getShipperColor,
} from "./hooks/useVrpState";

const AUTH_REQUIRED_MESSAGE = "Vui lòng đăng nhập Google để tối ưu quãng đường.";

export default function App() {
  const { configured: authConfigured, loading: authLoading, user } = useAuth();
  const isAuthenticated = Boolean(user);
  const canUseVrp = !authConfigured || isAuthenticated;

  const {
    placementMode,
    setPlacementMode,
    orderStep,
    pendingPickup,
    orders,
    shippers,
    selectedShipperId,
    selectedOrderIds,
    tourResult,
    status,
    errorMessage,
    avoidRoadTypes,
    setAvoidRoadTypes,
    canOptimize,
    setPickupForNewOrder,
    setDropoffForPendingOrder,
    cancelPendingPickup,
    addShipper,
    removeOrder,
    removeShipper,
    clearAll,
    selectShipper,
    toggleOrderSelection,
    beginRequest,
    completeRequest,
    failRequest,
    getScenarioSnapshot,
    loadScenario,
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
    mutationFn: postTours,
    onMutate: () => {
      beginRequest();
    },
    onSuccess: (data) => {
      completeRequest(data);
    },
    onError: (error) => {
      if (error?.status === 401) {
        failRequest(AUTH_REQUIRED_MESSAGE);
        return;
      }
      failRequest(error?.message || "Có lỗi xảy ra khi tối ưu.");
    },
  });

  const handleMapClick = useCallback(
    (rawPoint) => {
      if (!boundsLoaded || !canUseVrp) {
        if (!canUseVrp && authConfigured) {
          failRequest(AUTH_REQUIRED_MESSAGE);
        }
        return;
      }
      const candidate = {
        latitude: rawPoint.lat,
        longitude: rawPoint.lng,
      };
      if (!isInsideBbox(candidate, bbox)) {
        failRequest(ACCEPTED_AREA_DETAIL);
        return;
      }

      if (placementMode === PLACEMENT_MODE.ORDER) {
        if (pendingPickup) {
          setDropoffForPendingOrder(candidate);
        } else {
          setPickupForNewOrder(candidate);
        }
      } else {
        addShipper(candidate);
      }
    },
    [
      boundsLoaded,
      canUseVrp,
      authConfigured,
      bbox,
      placementMode,
      pendingPickup,
      setPickupForNewOrder,
      setDropoffForPendingOrder,
      addShipper,
      failRequest,
    ]
  );

  const handleOptimize = useCallback(() => {
    if (!canUseVrp) {
      failRequest(AUTH_REQUIRED_MESSAGE);
      return;
    }
    if (!canOptimize) return;
    const shipper = shippers.find((s) => s.id === selectedShipperId);
    if (!shipper) return;

    const assignedOrders = orders.filter((o) =>
      selectedOrderIds.includes(o.id)
    );

    mutation.mutate({
      shipper: {
        id: shipper.id,
        location: shipper.location,
      },
      orders: assignedOrders.map((o) => ({
        id: o.id,
        pickup: o.pickup,
        dropoff: o.dropoff,
      })),
      options: {
        avoid_road_types: avoidRoadTypes,
        avoid_edge_ids: [],
      },
    });
  }, [
    canUseVrp,
    canOptimize,
    mutation,
    shippers,
    selectedShipperId,
    orders,
    selectedOrderIds,
    avoidRoadTypes,
  ]);

  const handlePlacementModeChange = useCallback(
    (mode) => {
      if (mode !== PLACEMENT_MODE.ORDER && pendingPickup) {
        cancelPendingPickup();
      }
      setPlacementMode(mode);
    },
    [pendingPickup, cancelPendingPickup, setPlacementMode]
  );

  const statusText = useMemo(() => {
    if (authConfigured && !authLoading && !isAuthenticated) {
      return AUTH_REQUIRED_MESSAGE;
    }
    if (!boundsLoaded) return "Đang tải vùng hỗ trợ...";
    if (status === VRP_STATUS.LOADING) return "Đang tối ưu quãng đường...";
    if (status === VRP_STATUS.ERROR) return errorMessage;
    if (status === VRP_STATUS.SUCCESS && tourResult) {
      return `${getShipperGlyph(tourResult.shipper_id)}: ${formatDistance(tourResult.total_distance_meters)} (${selectedOrderIds.length} đơn)`;
    }
    return "Chọn shipper, tick đơn cần giao, rồi bấm \"Tối ưu quãng đường\".";
  }, [
    authConfigured,
    authLoading,
    isAuthenticated,
    boundsLoaded,
    status,
    errorMessage,
    tourResult,
    selectedOrderIds.length,
  ]);

  const shipperColorMap = useMemo(() => {
    const map = {};
    shippers.forEach((s, i) => {
      map[s.id] = getShipperColor(i);
    });
    return map;
  }, [shippers]);

  const selectedOrderLabels = useMemo(
    () => selectedOrderIds.map((id) => getOrderLabel(id)).join(", "),
    [selectedOrderIds]
  );

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-top">
          <h1>VRP Delivery Routing</h1>
          <AuthPanel />
        </div>
        <p>
          Mỗi đơn P1→D1, P2→D2… mỗi shipper S1, S2… Chọn shipper, tick đơn
          cần giao, bấm tối ưu để xem quãng đường.
        </p>
      </header>

      <main className="app-content">
        <section className="map-panel">
          <MapView
            bounds={bbox}
            orders={orders}
            shippers={shippers}
            pendingPickup={pendingPickup}
            tourResult={tourResult}
            selectedShipperId={selectedShipperId}
            selectedOrderIds={selectedOrderIds}
            shipperColorMap={shipperColorMap}
            selectionEnabled={boundsLoaded && canUseVrp}
            onAddPoint={handleMapClick}
          />
          {!canUseVrp && authConfigured && !authLoading ? (
            <div className="map-auth-overlay">
              <p>Đăng nhập Google để thêm điểm và tối ưu quãng đường.</p>
            </div>
          ) : null}
        </section>

        <aside className="side-panel">
          <ScenarioPanel
            user={user}
            scenarioSnapshot={getScenarioSnapshot}
            onLoadScenario={loadScenario}
            onAddPresetShipper={addShipper}
          />

          <ModeSwitcher
            placementMode={placementMode}
            onPlacementModeChange={handlePlacementModeChange}
            orderStep={orderStep}
            onCancelPendingPickup={cancelPendingPickup}
          />

          <OptionsPanel
            avoidRoadTypes={avoidRoadTypes}
            onAvoidRoadTypesChange={setAvoidRoadTypes}
          />

          <ShipperAssignmentPanel
            shippers={shippers}
            orders={orders}
            selectedShipperId={selectedShipperId}
            selectedOrderIds={selectedOrderIds}
            shipperColorMap={shipperColorMap}
            status={status}
            canOptimize={canOptimize && canUseVrp}
            onSelectShipper={selectShipper}
            onToggleOrder={toggleOrderSelection}
            onOptimize={handleOptimize}
          />

          <div className="panel-card controls-card">
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
            selectedOrderIds={selectedOrderIds}
            onRemoveOrder={removeOrder}
            onRemoveShipper={removeShipper}
          />

          {status === VRP_STATUS.SUCCESS && tourResult ? (
            <TourResultPanel
              tourResult={tourResult}
              orders={orders}
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
              {selectedShipperId && selectedOrderIds.length > 0 && (
                <p className="helper-text">
                  {getShipperGlyph(selectedShipperId)} ({getShipperLabel(selectedShipperId)})
                  {" "}nhận: {selectedOrderLabels}
                </p>
              )}
              <p className="empty-text" style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
                API: {API_BASE_URL}
              </p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}