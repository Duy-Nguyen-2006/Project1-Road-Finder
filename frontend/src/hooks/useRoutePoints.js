import { useState } from "react";

export const SELECTION_MODES = {
  START: "start",
  END: "end",
  WAYPOINT: "waypoint",
};

export function useRoutePoints() {
  const [selectionMode, setSelectionMode] = useState(SELECTION_MODES.START);
  const [startPoint, setStartPoint] = useState(null);
  const [endPoint, setEndPoint] = useState(null);
  const [waypoints, setWaypoints] = useState([]);
  const [orderedPoints, setOrderedPoints] = useState([]);

  const selectedPoints = [startPoint, ...waypoints, endPoint].filter(Boolean);

  const addPoint = (point) => {
    const pointWithRole = {
      ...point,
      role: selectionMode,
    };

    if (selectionMode === SELECTION_MODES.START) {
      setStartPoint(pointWithRole);
    } else if (selectionMode === SELECTION_MODES.END) {
      setEndPoint(pointWithRole);
    } else {
      setWaypoints((current) => [...current, pointWithRole]);
    }

    setOrderedPoints([]);
  };

  const removePoint = (role, index) => {
    if (role === SELECTION_MODES.START) {
      setStartPoint(null);
    } else if (role === SELECTION_MODES.END) {
      setEndPoint(null);
    } else {
      setWaypoints((current) => current.filter((_, currentIndex) => currentIndex !== index));
    }

    setOrderedPoints([]);
  };

  const clearPoints = () => {
    setStartPoint(null);
    setEndPoint(null);
    setWaypoints([]);
    setOrderedPoints([]);
  };

  const setRouteResult = (points) => {
    setOrderedPoints(points);
  };

  return {
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
  };
}
