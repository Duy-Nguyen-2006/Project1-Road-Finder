import React from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { SELECTION_MODES } from "../hooks/useRoutePoints";

// Fix Leaflet default icon issue with Vite/Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

const ROLE_STYLES = {
  [SELECTION_MODES.START]: {
    color: "#16a34a",
    fillColor: "#22c55e",
  },
  [SELECTION_MODES.END]: {
    color: "#dc2626",
    fillColor: "#ef4444",
  },
  [SELECTION_MODES.WAYPOINT]: {
    color: "#2563eb",
    fillColor: "#3b82f6",
  },
};

function MapClickHandler({ onAddPoint }) {
  useMapEvents({
    click(event) {
      onAddPoint({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });

  return null;
}

export default function MapView({ selectedPoints, orderedPoints, onAddPoint }) {
  const routePositions = orderedPoints.map((point) => [point.lat, point.lng]);

  return (
    <MapContainer center={[10.7769, 106.7009]} zoom={13} className="map-container">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapClickHandler onAddPoint={onAddPoint} />

      {selectedPoints.map((point, index) => {
        const style = ROLE_STYLES[point.role] || ROLE_STYLES[SELECTION_MODES.WAYPOINT];
        const label = point.role === SELECTION_MODES.START ? "Start A" : point.role === SELECTION_MODES.END ? "End B" : `Waypoint ${index}`;

        return (
          <Marker key={`${point.role}-${point.lat}-${point.lng}-${index}`} position={[point.lat, point.lng]}>
            <Popup>{label}</Popup>
          </Marker>
        );
      })}

      {routePositions.length > 1 ? <Polyline positions={routePositions} pathOptions={{ color: "#ef4444", weight: 5 }} /> : null}
    </MapContainer>
  );
}
