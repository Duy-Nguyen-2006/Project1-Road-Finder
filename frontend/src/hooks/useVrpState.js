import { useCallback, useState } from "react";

export const PLACEMENT_MODE = {
  ORDER: "order",
  SHIPPER: "shipper",
};

export const ORDER_STEP = {
  SET_PICKUP: "set_pickup",
  SET_DROPOFF: "set_dropoff",
};

export const VRP_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

export const SHIPPER_COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#9333ea",
  "#ea580c",
  "#0891b2",
  "#ca8a04",
  "#e11d48",
];

export function getShipperColor(index) {
  return SHIPPER_COLORS[index % SHIPPER_COLORS.length];
}

let _nextShipperId = 1;
let _nextOrderId = 1;

function clearTourOnEdit(setTourResult, setStatus, setErrorMessage) {
  setTourResult(null);
  setStatus(VRP_STATUS.IDLE);
  setErrorMessage("");
}

export function useVrpState() {
  const [placementMode, setPlacementMode] = useState(PLACEMENT_MODE.ORDER);
  const [pendingPickup, setPendingPickup] = useState(null);
  const [orders, setOrders] = useState([]);
  const [shippers, setShippers] = useState([]);
  const [selectedShipperId, setSelectedShipperId] = useState(null);
  const [selectedOrderIds, setSelectedOrderIds] = useState([]);
  const [tourResult, setTourResult] = useState(null);
  const [status, setStatus] = useState(VRP_STATUS.IDLE);
  const [errorMessage, setErrorMessage] = useState("");
  const [avoidRoadTypes, setAvoidRoadTypes] = useState([]);

  const resetTour = useCallback(() => {
    clearTourOnEdit(setTourResult, setStatus, setErrorMessage);
  }, []);

  const setPickupForNewOrder = useCallback((point) => {
    setPendingPickup(point);
    setErrorMessage("");
  }, []);

  const setDropoffForPendingOrder = useCallback((point) => {
    if (!pendingPickup) return;
    const orderId = `o${_nextOrderId++}`;
    setOrders((prev) => [
      ...prev,
      { id: orderId, pickup: pendingPickup, dropoff: point },
    ]);
    setPendingPickup(null);
    resetTour();
  }, [pendingPickup, resetTour]);

  const cancelPendingPickup = useCallback(() => {
    setPendingPickup(null);
    setErrorMessage("");
  }, []);

  const addShipper = useCallback((point) => {
    const newShipper = {
      id: `s${_nextShipperId++}`,
      location: point,
    };
    setShippers((prev) => [...prev, newShipper]);
    setSelectedShipperId((current) => current ?? newShipper.id);
    resetTour();
  }, [resetTour]);

  const removeOrder = useCallback((orderId) => {
    setOrders((prev) => prev.filter((o) => o.id !== orderId));
    setSelectedOrderIds((prev) => prev.filter((id) => id !== orderId));
    resetTour();
  }, [resetTour]);

  const removeShipper = useCallback((shipperId) => {
    setShippers((prev) => {
      const next = prev.filter((s) => s.id !== shipperId);
      setSelectedShipperId((current) => {
        if (current !== shipperId) return current;
        return next[0]?.id ?? null;
      });
      return next;
    });
    resetTour();
  }, [resetTour]);

  const clearAll = useCallback(() => {
    setOrders([]);
    setShippers([]);
    setPendingPickup(null);
    setSelectedShipperId(null);
    setSelectedOrderIds([]);
    setTourResult(null);
    setStatus(VRP_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const selectShipper = useCallback((shipperId) => {
    setSelectedShipperId(shipperId);
    resetTour();
  }, [resetTour]);

  const toggleOrderSelection = useCallback((orderId) => {
    setSelectedOrderIds((prev) =>
      prev.includes(orderId)
        ? prev.filter((id) => id !== orderId)
        : [...prev, orderId]
    );
    resetTour();
  }, [resetTour]);

  const beginRequest = useCallback(() => {
    setStatus(VRP_STATUS.LOADING);
    setErrorMessage("");
  }, []);

  const completeRequest = useCallback((data) => {
    setTourResult(data);
    setStatus(VRP_STATUS.SUCCESS);
    setErrorMessage("");
  }, []);

  const failRequest = useCallback((message) => {
    setStatus(VRP_STATUS.ERROR);
    setErrorMessage(message || "Có lỗi xảy ra.");
  }, []);

  const canOptimize =
    Boolean(selectedShipperId) &&
    selectedOrderIds.length > 0 &&
    status !== VRP_STATUS.LOADING;

  const orderStep = pendingPickup
    ? ORDER_STEP.SET_DROPOFF
    : ORDER_STEP.SET_PICKUP;

  return {
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
  };
}