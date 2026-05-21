import { MapContainer, Marker, Polyline, TileLayer, useMapEvents } from "react-leaflet";

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
  const markerPositions = selectedPoints.map((point) => [point.lat, point.lng]);

  return (
    <MapContainer center={[10.7769, 106.7009]} zoom={13} className="map-container">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapClickHandler onAddPoint={onAddPoint} />

      {markerPositions.map((position, index) => (
        <Marker key={`${position[0]}-${position[1]}-${index}`} position={position} />
      ))}

      {routePositions.length > 1 ? <Polyline positions={routePositions} pathOptions={{ color: "#ef4444", weight: 5 }} /> : null}
    </MapContainer>
  );
}
