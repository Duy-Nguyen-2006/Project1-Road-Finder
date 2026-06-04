import { useCallback, useState } from "react";

export const SELECTION_MODES = {
  START: "start",
  END: "end",
};

export const ROUTE_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

const EMPTY_ROUTE = null;

export function useRoutePoints() {
  const [selectionMode, setSelectionMode] = useState(SELECTION_MODES.START);
  const [startPoint, setStartPoint] = useState(null);
  const [endPoint, setEndPoint] = useState(null);
  const [route, setRoute] = useState(EMPTY_ROUTE);
  const [status, setStatus] = useState(ROUTE_STATUS.IDLE);
  const [errorMessage, setErrorMessage] = useState("");

  const _setPoint = useCallback(
    (mode, point) => {
      if (mode === SELECTION_MODES.START) {
        setStartPoint(point);
        setRoute(EMPTY_ROUTE);
      } else if (mode === SELECTION_MODES.END) {
        setEndPoint(point);
        setRoute(EMPTY_ROUTE);
      }
    },
    []
  );

  const addPoint = useCallback(
    (point) => {
      const pointWithRole = {
        latitude: point.lat,
        longitude: point.lng,
        role: selectionMode,
      };
      _setPoint(selectionMode, pointWithRole);
      setStatus(ROUTE_STATUS.IDLE);
      setErrorMessage("");
    },
    [selectionMode, _setPoint]
  );

  const removePoint = useCallback((role) => {
    if (role === SELECTION_MODES.START) {
      setStartPoint(null);
    } else if (role === SELECTION_MODES.END) {
      setEndPoint(null);
    }
    setRoute(EMPTY_ROUTE);
    setStatus(ROUTE_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const clearAll = useCallback(() => {
    setStartPoint(null);
    setEndPoint(null);
    setRoute(EMPTY_ROUTE);
    setStatus(ROUTE_STATUS.IDLE);
    setErrorMessage("");
  }, []);

  const beginRouteRequest = useCallback(() => {
    setStatus(ROUTE_STATUS.LOADING);
    setErrorMessage("");
  }, []);

  const completeRouteRequest = useCallback((response) => {
    setRoute(response);
    setStatus(ROUTE_STATUS.SUCCESS);
    setErrorMessage("");
  }, []);

  const failRouteRequest = useCallback((message) => {
    setStatus(ROUTE_STATUS.ERROR);
    setErrorMessage(message || "Có lỗi xảy ra khi tìm đường.");
  }, []);

  const canFindRoute =
    Boolean(startPoint && endPoint) &&
    (status === ROUTE_STATUS.IDLE || status === ROUTE_STATUS.ERROR || status === ROUTE_STATUS.SUCCESS);

  return {
    selectionMode,
    setSelectionMode,
    startPoint,
    endPoint,
    route,
    status,
    errorMessage,
    canFindRoute,
    addPoint,
    removePoint,
    clearAll,
    beginRouteRequest,
    completeRouteRequest,
    failRouteRequest,
  };
}
