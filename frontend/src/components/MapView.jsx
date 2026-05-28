import React, { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, useMapEvents } from "react-leaflet";
import { SELECTION_MODES } from "../hooks/useRoutePoints";
import { fetchIntersections } from "../api/routeApi";

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
  const [intersections, setIntersections] = useState([]);
  const [loadingIntersections, setLoadingIntersections] = useState(false);

  useEffect(() => {
    async function loadIntersections() {
      setLoadingIntersections(true);
      try {
        // Default bounding box for Ho Chi Minh City area
        const bbox = "10.70,106.60,10.85,106.80";
        const data = await fetchIntersections("Ho Chi Minh City", bbox);
        setIntersections(data.intersections || []);
      } catch (error) {
        console.error("Failed to load intersections:", error);
      } finally {
        setLoadingIntersections(false);
      }
    }

    loadIntersections();
  }, []);

  return (
    <MapContainer center={[10.7769, 106.7009]} zoom={13} className="map-container">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapClickHandler onAddPoint={onAddPoint} />

      {/* Display all intersections as small markers */}
      {intersections.map((intersection, index) => (
        <CircleMarker
          key={`intersection-${index}`}
          center={[intersection.latitude, intersection.longitude]}
          radius={3}
          pathOptions={{ color: "#6b7280", fillColor: "#9ca3af", fillOpacity: 0.5 }}
        />
      ))}

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

      {loadingIntersections && (
        <div style={{ position: 'absolute', top: '10px', right: '10px', background: 'white', padding: '10px', borderRadius: '5px', zIndex: 1000 }}>
          Đang tải giao lộ...
        </div>
      )}
    </MapContainer>
  );
}
