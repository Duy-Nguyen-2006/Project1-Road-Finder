import React from "react";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, useMapEvents } from "react-leaflet";
import { SELECTION_MODES } from "../hooks/useRoutePoints";

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
          <React.Fragment key={`${point.role}-${point.lat}-${point.lng}-${index}`}>
            <Marker position={[point.lat, point.lng]}>
              <Popup>{label}</Popup>
            </Marker>
            <CircleMarker
              center={[point.lat, point.lng]}
              radius={9}
              pathOptions={{ color: style.color, fillColor: style.fillColor, fillOpacity: 0.9 }}
            />
          </React.Fragment>
        );
      })}

      {routePositions.length > 1 ? <Polyline positions={routePositions} pathOptions={{ color: "#ef4444", weight: 5 }} /> : null}
    </MapContainer>
  );
}
