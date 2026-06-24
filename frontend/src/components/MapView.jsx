import React, { useEffect, useMemo } from "react";
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
import PropTypes from "prop-types";
import { bboxToLeaflet } from "../utils/geo";
import {
  CoordPropType,
  FleetResultPropType,
  OrderPropType,
  ShipperColorMapPropType,
  ShipperPropType,
} from "./proptypes";

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

// Custom marker icons
function createIcon(color) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="
      width: 16px;
      height: 16px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

const PICKUP_ICON = createIcon("#16a34a");
const DROPOFF_ICON = createIcon("#dc2626");
const SHIPPER_ICON = createIcon("#2563eb");
const PENDING_ICON = createIcon("#f59e0b");

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

MapClickHandler.propTypes = {
  enabled: PropTypes.bool.isRequired,
  onAddPoint: PropTypes.func.isRequired,
};

function MapBoundsFitter({ bounds, tourPolylines }) {
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
    const allPoints = tourPolylines.flatMap((tour) => tour.points);
    if (allPoints.length > 1) {
      map.fitBounds(allPoints, { padding: [32, 32] });
    }
  }, [tourPolylines, map]);

  return null;
}

MapBoundsFitter.propTypes = {
  bounds: PropTypes.shape({
    min_latitude: PropTypes.number,
    min_longitude: PropTypes.number,
    max_latitude: PropTypes.number,
    max_longitude: PropTypes.number,
  }),
  tourPolylines: PropTypes.arrayOf(
    PropTypes.shape({
      shipperId: PropTypes.string,
      points: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.number)),
      color: PropTypes.string,
    })
  ).isRequired,
};

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
  orders,
  shippers,
  pendingPickup,
  fleetResult,
  shipperColorMap,
  selectionEnabled,
  onAddPoint,
  placementMode,
}) {
  const rectangleBounds = useMemo(() => bboxToLeaflet(bounds), [bounds]);

  // Build polylines from fleet result
  const tourPolylines = useMemo(() => {
    if (!fleetResult?.tours) return [];
    return fleetResult.tours.map((tour) => {
      const points = [];
      for (const leg of tour.legs) {
        for (const p of leg.route_points) {
          points.push([p.latitude, p.longitude]);
        }
      }
      return {
        shipperId: tour.shipper_id,
        points,
        color: shipperColorMap?.[tour.shipper_id] ?? "#666",
      };
    });
  }, [fleetResult, shipperColorMap]);

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
      <MapBoundsFitter bounds={bounds} tourPolylines={tourPolylines} />

      {rectangleBounds ? (
        <Rectangle
          bounds={rectangleBounds}
          pathOptions={{ color: "red", weight: 2, fillOpacity: 0.05 }}
        />
      ) : null}

      {/* Shipper markers */}
      {shippers.map((s) => (
        <Marker
          key={`shipper-${s.id}`}
          position={[s.location.latitude, s.location.longitude]}
          icon={SHIPPER_ICON}
        >
          <Popup>
            <strong>{s.id}</strong> (Shipper)
          </Popup>
        </Marker>
      ))}

      {/* Order markers */}
      {orders.map((o) => (
        <React.Fragment key={o.id}>
          <Marker
            position={[o.pickup.latitude, o.pickup.longitude]}
            icon={PICKUP_ICON}
          >
            <Popup>
              <strong>{o.id}</strong> - Lấy hàng
            </Popup>
          </Marker>
          <Marker
            position={[o.dropoff.latitude, o.dropoff.longitude]}
            icon={DROPOFF_ICON}
          >
            <Popup>
              <strong>{o.id}</strong> - Giao hàng
            </Popup>
          </Marker>
        </React.Fragment>
      ))}

      {/* Pending pickup marker */}
      {pendingPickup && (
        <Marker
          position={[pendingPickup.latitude, pendingPickup.longitude]}
          icon={PENDING_ICON}
        >
          <Popup>Điểm lấy hàng (chờ chọn điểm giao)</Popup>
        </Marker>
      )}

      {/* Tour polylines */}
      {tourPolylines.map((tp) =>
        tp.points.length > 1 ? (
          <Polyline
            key={`tour-${tp.shipperId}`}
            positions={tp.points}
            pathOptions={{ color: tp.color, weight: 4, opacity: 0.8 }}
          />
        ) : null
      )}
    </MapContainer>
  );
}

MapView.propTypes = {
  bounds: PropTypes.shape({
    min_latitude: PropTypes.number,
    min_longitude: PropTypes.number,
    max_latitude: PropTypes.number,
    max_longitude: PropTypes.number,
  }),
  orders: PropTypes.arrayOf(OrderPropType).isRequired,
  shippers: PropTypes.arrayOf(ShipperPropType).isRequired,
  pendingPickup: CoordPropType,
  fleetResult: FleetResultPropType,
  shipperColorMap: ShipperColorMapPropType,
  selectionEnabled: PropTypes.bool.isRequired,
  onAddPoint: PropTypes.func.isRequired,
  placementMode: PropTypes.string,
};
