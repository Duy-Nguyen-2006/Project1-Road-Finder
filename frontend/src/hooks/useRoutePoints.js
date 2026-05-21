import { useState } from "react";

export function useRoutePoints() {
  const [selectedPoints, setSelectedPoints] = useState([]);
  const [orderedPoints, setOrderedPoints] = useState([]);

  const addPoint = (point) => {
    setSelectedPoints((current) => [...current, point]);
    setOrderedPoints([]);
  };

  const removePoint = (index) => {
    setSelectedPoints((current) => current.filter((_, currentIndex) => currentIndex !== index));
    setOrderedPoints([]);
  };

  const clearPoints = () => {
    setSelectedPoints([]);
    setOrderedPoints([]);
  };

  const setRouteResult = (points) => {
    setOrderedPoints(points);
  };

  return {
    selectedPoints,
    orderedPoints,
    addPoint,
    removePoint,
    clearPoints,
    setRouteResult,
  };
}
