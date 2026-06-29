import { useCallback, useMemo, useState } from "react";

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

export const UNASSIGNED_ORDER_COLOR = "#9ca3af";

export function getShipperColor(index) {
  return SHIPPER_COLORS[index % SHIPPER_COLORS.length];
}

let _nextShipperId = 1;
let _nextOrderId = 1;

function _maxIdNumber(items, prefix) {
  let max = 0;
  for (const item of items) {
    const match = item.id?.match(new RegExp(String.raw`^${prefix}(\d+)$`));
    if (match) {
      max = Math.max(max, Number.parseInt(match[1], 10));
    }
  }
  return max;
}

function syncIdCounters(orders, shippers) {
  _nextOrderId = _maxIdNumber(orders, "o") + 1;
  _nextShipperId = _maxIdNumber(shippers, "s") + 1;
}

function clearTourOnEdit(setTourResults, setStatus, setErrorMessage) {
  setTourResults([]);
  setStatus(VRP_STATUS.IDLE);
  setErrorMessage("");
}

function migrateOrderAssignments(payload) {
  if (payload?.orderAssignments) {
    return payload.orderAssignments;
  }
  if (payload?.selectedShipperId && payload?.selectedOrderIds?.length) {
    const map = {};
    for (const orderId of payload.selectedOrderIds) {
      map[orderId] = payload.selectedShipperId;
    }
    return map;
  }
  return {};
}

export function useVrpState() {
  const [placementMode, setPlacementMode] = useState(PLACEMENT_MODE.ORDER);
  const [pendingPickup, setPendingPickup] = useState(null);
  const [orders, setOrders] = useState([]);
  const [shippers, setShippers] = useState([]);
  const [selectedShipperId, setSelectedShipperId] = useState(null);
  const [orderAssignments, setOrderAssignments] = useState({});
  const [tourResults, setTourResults] = useState([]);
  const [status, setStatus] = useState(VRP_STATUS.IDLE);
  const [errorMessage, setErrorMessage] = useState("");
  const [avoidRoadTypes, setAvoidRoadTypes] = useState([]);

  const selectedOrderIds = useMemo(() => {
    if (!selectedShipperId) return [];
    return Object.entries(orderAssignments)
      .filter(([, shipperId]) => shipperId === selectedShipperId)
      .map(([orderId]) => orderId);
  }, [orderAssignments, selectedShipperId]);

  const resetTour = useCallback(() => {
    clearTourOnEdit(setTourResults, setStatus, setErrorMessage);
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
    setOrderAssignments((prev) => {
      if (!prev[orderId]) return prev;
      const next = { ...prev };
      delete next[orderId];
      return next;
    });
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
    setOrderAssignments((prev) => {
      const next = { ...prev };
      for (const [orderId, ownerId] of Object.entries(next)) {
        if (ownerId === shipperId) {
          delete next[orderId];
        }
      }
      return next;
    });
    resetTour();
  }, [resetTour]);

  const clearAll = useCallback(() => {
    setOrders([]);
    setShippers([]);
    setPendingPickup(null);
    setSelectedShipperId(null);
    setOrderAssignments({});
    setTourResults([]);
    setStatus(VRP_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const selectShipper = useCallback((shipperId) => {
    setSelectedShipperId(shipperId);
    resetTour();
  }, [resetTour]);

  const toggleOrderSelection = useCallback(
    (orderId) => {
      if (!selectedShipperId) return;
      setOrderAssignments((prev) => {
        const owner = prev[orderId];
        if (owner === selectedShipperId) {
          const next = { ...prev };
          delete next[orderId];
          return next;
        }
        if (owner && owner !== selectedShipperId) {
          return prev;
        }
        return { ...prev, [orderId]: selectedShipperId };
      });
      resetTour();
    },
    [selectedShipperId, resetTour]
  );

  const beginRequest = useCallback(() => {
    setStatus(VRP_STATUS.LOADING);
    setErrorMessage("");
  }, []);

  const completeRequest = useCallback((data) => {
    setTourResults(Array.isArray(data) ? data : [data]);
    setStatus(VRP_STATUS.SUCCESS);
    setErrorMessage("");
  }, []);

  const failRequest = useCallback((message) => {
    setStatus(VRP_STATUS.ERROR);
    setErrorMessage(message || "Có lỗi xảy ra.");
  }, []);

  const getScenarioSnapshot = useCallback(
    () => ({
      orders,
      shippers,
      selectedShipperId,
      orderAssignments,
      avoidRoadTypes,
    }),
    [orders, shippers, selectedShipperId, orderAssignments, avoidRoadTypes]
  );

  const loadScenario = useCallback((payload) => {
    const nextOrders = payload?.orders ?? [];
    const nextShippers = payload?.shippers ?? [];
    syncIdCounters(nextOrders, nextShippers);
    setOrders(nextOrders);
    setShippers(nextShippers);
    setSelectedShipperId(
      payload?.selectedShipperId ?? nextShippers[0]?.id ?? null
    );
    setOrderAssignments(migrateOrderAssignments(payload));
    setAvoidRoadTypes(payload?.avoidRoadTypes ?? []);
    setPendingPickup(null);
    setTourResults([]);
    setStatus(VRP_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const canOptimize =
    Object.keys(orderAssignments).length > 0 &&
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
    orderAssignments,
    tourResults,
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
  };
}