import { useCallback, useState } from "react";

export const PLACEMENT_MODE = {
  ORDER: "order",
  SHIPPER: "shipper",
};

export const ORDER_STEP = {
  PICKUP: "pickup",
  DROPOFF: "dropoff",
};

export const VRP_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

// Fixed color palette for shippers
export const SHIPPER_COLORS = [
  "#2563eb", // blue
  "#dc2626", // red
  "#16a34a", // green
  "#9333ea", // purple
  "#ea580c", // orange
  "#0891b2", // cyan
  "#ca8a04", // yellow
  "#e11d48", // rose
];

export function getShipperColor(index) {
  return SHIPPER_COLORS[index % SHIPPER_COLORS.length];
}

let _nextOrderId = 1;
let _nextShipperId = 1;

export function useVrpState() {
  const [placementMode, setPlacementMode] = useState(PLACEMENT_MODE.ORDER);
  const [orderStep, setOrderStep] = useState(ORDER_STEP.PICKUP);
  const [orders, setOrders] = useState([]);
  const [shippers, setShippers] = useState([]);
  const [pendingPickup, setPendingPickup] = useState(null);
  const [fleetResult, setFleetResult] = useState(null);
  const [status, setStatus] = useState(VRP_STATUS.IDLE);
  const [errorMessage, setErrorMessage] = useState("");
  const [avoidRoadTypes, setAvoidRoadTypes] = useState([]);

  const addPickup = useCallback((point) => {
    setPendingPickup(point);
    setOrderStep(ORDER_STEP.DROPOFF);
  }, []);

  const addDropoff = useCallback(
    (point) => {
      if (!pendingPickup) return;
      const newOrder = {
        id: `o${_nextOrderId++}`,
        pickup: pendingPickup,
        dropoff: point,
      };
      setOrders((prev) => [...prev, newOrder]);
      setPendingPickup(null);
      setOrderStep(ORDER_STEP.PICKUP);
      setFleetResult(null);
      setStatus(VRP_STATUS.IDLE);
    },
    [pendingPickup]
  );

  const addShipper = useCallback((point) => {
    const newShipper = {
      id: `s${_nextShipperId++}`,
      location: point,
    };
    setShippers((prev) => [...prev, newShipper]);
    setFleetResult(null);
    setStatus(VRP_STATUS.IDLE);
  }, []);

  const removeOrder = useCallback((orderId) => {
    setOrders((prev) => prev.filter((o) => o.id !== orderId));
    setFleetResult(null);
    setStatus(VRP_STATUS.IDLE);
  }, []);

  const removeShipper = useCallback((shipperId) => {
    setShippers((prev) => prev.filter((s) => s.id !== shipperId));
    setFleetResult(null);
    setStatus(VRP_STATUS.IDLE);
  }, []);

  const clearAll = useCallback(() => {
    setOrders([]);
    setShippers([]);
    setPendingPickup(null);
    setOrderStep(ORDER_STEP.PICKUP);
    setFleetResult(null);
    setStatus(VRP_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const beginRequest = useCallback(() => {
    setStatus(VRP_STATUS.LOADING);
    setErrorMessage("");
  }, []);

  const completeRequest = useCallback((data) => {
    setFleetResult(data);
    setStatus(VRP_STATUS.SUCCESS);
    setErrorMessage("");
  }, []);

  const failRequest = useCallback((message) => {
    setStatus(VRP_STATUS.ERROR);
    setErrorMessage(message || "Có lỗi xảy ra.");
  }, []);

  const canOptimize =
    orders.length > 0 &&
    shippers.length > 0 &&
    status !== VRP_STATUS.LOADING;

  return {
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
  };
}
