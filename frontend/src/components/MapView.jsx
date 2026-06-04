import React, { useEffect } from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  Rectangle,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { SELECTION_MODES } from "../hooks/useRoutePoints";
import { bboxToLeaflet, routePointsToLeaflet } from "../utils/geo";

// Fix Leaflet default icon issue with Vite/Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

const ROLE_COLORS = {
  [SELECTION_MODES.START]: { color: "#16a34a", fillColor: "#22c55e" },
  [SELECTION_MODES.END]: { color: "#dc2626", fillColor: "#ef4444" },
};

const ROLE_LABELS = {
  [SELECTION_MODES.START]: "Start",
  [SELECTION_MODES.END]: "End",
};

const DEFAULT_CENTER = [10.7769, 106.7009];
const DEFAULT_ZOOM = 13;

function MapClickHandler({ enabled, onAddPoint }) {
  useMapEvents({
    click(event) {
      if (!enabled) return;
      onAddPoint({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });
  return null;
}

function MapBoundsFitter({ bounds, routePoints }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      const latlngs = bboxToLeaflet(bounds);
      if (latlngs) {
        map.fitBounds(latlngs, { padding: [24, 24] });
      }
    }
  }, [bounds, map]);

  useEffect(() => {
    if (Array.isArray(routePoints) && routePoints.length > 1) {
      map.fitBounds(routePoints, { padding: [32, 32] });
    }
  }, [routePoints, map]);

  return null;
}

function MapInvalidator() {
  const map = useMap();
  useEffect(() => {
    const handle = setTimeout(() => map.invalidateSize(), 50);
    return () => clearTimeout(handle);
  }, [map]);
  return null;
}

export default function MapView({
  bounds,
  startPoint,
  endPoint,
  routePoints,
  selectionEnabled,
  onAddPoint,
}) {
  const rectangleBounds = bboxToLeaflet(bounds);
  const polylinePositions = routePointsToLeaflet(routePoints);

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="map-container"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapInvalidator />
      <MapClickHandler enabled={selectionEnabled} onAddPoint={onAddPoint} />
      <MapBoundsFitter bounds={bounds} routePoints={polylinePositions} />

      {rectangleBounds ? (
        <Rectangle
          bounds={rectangleBounds}
          pathOptions={{ color: "red", weight: 2, fillOpacity: 0.05 }}
        />
      ) : null}

      {startPoint ? (
        <Marker
          key={`start-${startPoint.latitude}-${startPoint.longitude}`}
          position={[startPoint.latitude, startPoint.longitude]}
        >
          <Popup>Start</Popup>
        </Marker>
      ) : null}

      {endPoint ? (
        <Marker
          key={`end-${endPoint.latitude}-${endPoint.longitude}`}
          position={[endPoint.latitude, endPoint.longitude]}
        >
          <Popup>End</Popup>
        </Marker>
      ) : null}

      {polylinePositions.length > 1 ? (
        <Polyline
          positions={polylinePositions}
          pathOptions={{ color: "#2563eb", weight: 5 }}
        />
      ) : null}
    </MapContainer>
  );
}
