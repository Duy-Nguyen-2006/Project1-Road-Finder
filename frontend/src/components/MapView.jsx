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
  getDropoffGlyph,
  getOrderDisplayColor,
  getOrderLabel,
  getPickupGlyph,
} from "../utils/orders";
import {
  getShipperGlyph,
  getShipperLabel,
} from "../utils/shippers";
import { buildTourDisplayData } from "../utils/tourDisplay";
import {
  CoordPropType,
  OrderAssignmentsPropType,
  OrderPropType,
  ShipperColorMapPropType,
  ShipperPropType,
  TourResultsPropType,
} from "./proptypes";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

function pinIcon({ color, glyph, selected = false, sequence = null }) {
  const ring = selected
    ? `<circle cx="16" cy="15" r="13" fill="none" stroke="#000" stroke-width="2" opacity="0.35"/>`
    : "";
  const sequenceBadge =
    sequence != null
      ? `<circle cx="26" cy="6" r="8" fill="${color}" stroke="white" stroke-width="1.5"/>
         <text x="26" y="9.5" text-anchor="middle" font-size="9" font-weight="700" fill="white" font-family="Arial, sans-serif">${sequence}</text>`
      : "";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 42" width="32" height="42">
    <path d="M16 1 C8 1 2 7 2 15 C2 25 16 41 16 41 C16 41 30 25 30 15 C30 7 24 1 16 1 Z"
      fill="${color}" stroke="white" stroke-width="2.5"/>
    <circle cx="16" cy="15" r="9" fill="white"/>
    ${ring}
    <text x="16" y="20" text-anchor="middle" font-size="${glyph.length > 2 ? 10 : 12}" font-weight="700" fill="${color}" font-family="Arial, sans-serif">${glyph}</text>
    ${sequenceBadge}
  </svg>`;
  return L.divIcon({
    className: "marker-pin",
    html: svg,
    iconSize: [32, 42],
    iconAnchor: [16, 41],
    popupAnchor: [0, -36],
  });
}

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

function MapBoundsFitter({ bounds, allRoutePoints }) {
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
    if (allRoutePoints.length > 1) {
      map.fitBounds(allRoutePoints, { padding: [32, 32] });
    }
  }, [allRoutePoints, map]);

  return null;
}

MapBoundsFitter.propTypes = {
  bounds: PropTypes.shape({
    min_latitude: PropTypes.number,
    min_longitude: PropTypes.number,
    max_latitude: PropTypes.number,
    max_longitude: PropTypes.number,
  }),
  allRoutePoints: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.number))
    .isRequired,
};

function MapInvalidator() {
  const map = useMap();
  useEffect(() => {
    const handle = setTimeout(() => map.invalidateSize(), 50);
    return () => clearTimeout(handle);
  }, [map]);
  return null;
}

function legToLatLngs(leg) {
  return leg.route_points.map((p) => [p.latitude, p.longitude]);
}

export default function MapView({
  bounds,
  orders,
  shippers,
  pendingPickup,
  tourResults,
  orderAssignments,
  selectedShipperId,
  shipperColorMap,
  selectionEnabled,
  onAddPoint,
}) {
  const rectangleBounds = useMemo(() => bboxToLeaflet(bounds), [bounds]);

  const { stopLookup } = useMemo(
    () => buildTourDisplayData(tourResults),
    [tourResults]
  );

  const routeLegs = useMemo(() => {
    if (!tourResults?.length) return [];
    const legs = [];
    for (const tour of tourResults) {
      if (!tour.legs?.length) continue;
      const shipperColor = shipperColorMap?.[tour.shipper_id] ?? "#2563eb";
      tour.legs
        .filter((leg) => leg.route_points.length > 0)
        .forEach((leg, index) => {
          const isDropoff = leg.kind?.endsWith("_dropoff");
          legs.push({
            key: `${tour.shipper_id}-${leg.kind}-${index}`,
            points: legToLatLngs(leg),
            color: shipperColor,
            dashed: isDropoff,
          });
        });
    }
    return legs;
  }, [tourResults, shipperColorMap]);

  const allRoutePoints = useMemo(
    () => routeLegs.flatMap((leg) => leg.points),
    [routeLegs]
  );

  const pendingOrderNumber = orders.length + 1;

  const getStopSequence = (orderId, kind) => {
    const owner = orderAssignments[orderId];
    if (!owner) return null;
    return stopLookup[`${owner}:${orderId}:${kind}`] ?? null;
  };

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
      <MapBoundsFitter bounds={bounds} allRoutePoints={allRoutePoints} />

      {rectangleBounds ? (
        <Rectangle
          bounds={rectangleBounds}
          pathOptions={{ color: "red", weight: 2, fillOpacity: 0.05 }}
        />
      ) : null}

      {shippers.map((s) => {
        const color = shipperColorMap?.[s.id] ?? "#2563eb";
        const selected = s.id === selectedShipperId;
        const glyph = getShipperGlyph(s.id);
        const label = getShipperLabel(s.id);
        return (
          <Marker
            key={`shipper-${s.id}`}
            position={[s.location.latitude, s.location.longitude]}
            icon={pinIcon({
              color,
              glyph,
              selected,
            })}
            zIndexOffset={selected ? 1000 : 0}
          >
            <Popup>
              <strong>{label}</strong> ({glyph})
              {selected ? " — đang chọn" : ""}
            </Popup>
          </Marker>
        );
      })}

      {orders.map((o) => {
        const color = getOrderDisplayColor(
          o.id,
          orders,
          orderAssignments,
          shipperColorMap
        );
        const label = getOrderLabel(o.id);
        const owner = orderAssignments[o.id];
        const assignedToActive = owner === selectedShipperId;
        const pickupSequence = getStopSequence(o.id, "pickup");
        const dropoffSequence = getStopSequence(o.id, "dropoff");
        return (
          <React.Fragment key={o.id}>
            <Marker
              position={[o.pickup.latitude, o.pickup.longitude]}
              icon={pinIcon({
                color,
                glyph: getPickupGlyph(o.id),
                selected: assignedToActive,
                sequence: pickupSequence,
              })}
              zIndexOffset={assignedToActive ? 900 : 0}
            >
              <Popup>
                <strong>{label}</strong> — Lấy hàng ({getPickupGlyph(o.id)})
                {pickupSequence != null ? ` · điểm ${pickupSequence}` : ""}
                {owner ? ` · ${getShipperGlyph(owner)}` : " · chưa gán"}
              </Popup>
            </Marker>
            <Marker
              position={[o.dropoff.latitude, o.dropoff.longitude]}
              icon={pinIcon({
                color,
                glyph: getDropoffGlyph(o.id),
                selected: assignedToActive,
                sequence: dropoffSequence,
              })}
              zIndexOffset={assignedToActive ? 900 : 0}
            >
              <Popup>
                <strong>{label}</strong> — Giao hàng ({getDropoffGlyph(o.id)})
                {dropoffSequence != null ? ` · điểm ${dropoffSequence}` : ""}
                {owner ? ` · ${getShipperGlyph(owner)}` : " · chưa gán"}
              </Popup>
            </Marker>
          </React.Fragment>
        );
      })}

      {pendingPickup && (
        <Marker
          key="pending-pickup"
          position={[pendingPickup.latitude, pendingPickup.longitude]}
          icon={pinIcon({
            color: "#f59e0b",
            glyph: `P${pendingOrderNumber}`,
          })}
        >
          <Popup>
            Đơn {pendingOrderNumber} — chờ chọn điểm giao (D{pendingOrderNumber})
          </Popup>
        </Marker>
      )}

      {routeLegs.map((leg) => (
        <Polyline
          key={leg.key}
          positions={leg.points}
          pathOptions={{
            color: leg.color,
            weight: 5,
            opacity: 0.9,
            dashArray: leg.dashed ? "8 6" : undefined,
          }}
        />
      ))}
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
  tourResults: TourResultsPropType,
  orderAssignments: OrderAssignmentsPropType.isRequired,
  selectedShipperId: PropTypes.string,
  shipperColorMap: ShipperColorMapPropType,
  selectionEnabled: PropTypes.bool.isRequired,
  onAddPoint: PropTypes.func.isRequired,
};