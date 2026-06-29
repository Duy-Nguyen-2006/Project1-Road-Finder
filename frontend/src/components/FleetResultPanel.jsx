import React, { useMemo } from "react";
import { formatDistance } from "../utils/format";
import {
  FleetResultPropType,
  ShipperColorMapPropType,
} from "./proptypes";

function formatStopLabel(orderId, kind) {
  const suffix = orderId.replace(/^o/i, "");
  const prefix = kind === "pickup" ? "P" : "D";
  return `${prefix}${suffix}`;
}

export default function FleetResultPanel({ fleetResult, shipperColorMap }) {
  const { activeTours, idleTours } = useMemo(() => {
    const tours = fleetResult?.tours ?? [];
    return {
      activeTours: tours.filter((t) => t.ordered_stops.length > 0),
      idleTours: tours.filter((t) => t.ordered_stops.length === 0),
    };
  }, [fleetResult]);

  if (!fleetResult) return null;

  return (
    <div className="panel-card">
      <h2>Kết quả tối ưu</h2>
      <div className="fleet-result">
        <div className="fleet-total">
          Tổng quãng đường đội: {formatDistance(fleetResult.total_distance_meters)}
        </div>
        <p className="helper-text">
          Mỗi đơn (P/D) được gán cho một shipper — không gom toàn bộ đơn cho
          mọi người.
        </p>

        {activeTours.map((tour) => (
          <div key={tour.shipper_id} className="shipper-tour">
            <div className="shipper-tour-header">
              <span
                className="shipper-color-dot"
                style={{ background: shipperColorMap?.[tour.shipper_id] ?? "#666" }}
              />
              <span className="shipper-name">{tour.shipper_id}</span>
              <span className="shipper-distance">
                {formatDistance(tour.total_distance_meters)}
              </span>
            </div>
            <ul className="stop-list">
              {tour.ordered_stops.map((stop) => (
                <li
                  key={`${tour.shipper_id}-${stop.kind}-${stop.order_id}`}
                  className="stop-item"
                >
                  <span className={`stop-badge ${stop.kind}`}>
                    {stop.kind === "pickup" ? "Lấy" : "Giao"}
                  </span>
                  <span>{formatStopLabel(stop.order_id, stop.kind)}</span>
                  <span className="stop-order-id">({stop.order_id})</span>
                </li>
              ))}
            </ul>
          </div>
        ))}

        {idleTours.length > 0 && (
          <div className="idle-shippers-section">
            <h3>Shipper chưa được gán đơn</h3>
            <ul className="stop-list">
              {idleTours.map((tour) => (
                <li key={tour.shipper_id} className="stop-item">
                  <span
                    className="shipper-color-dot"
                    style={{ background: shipperColorMap?.[tour.shipper_id] ?? "#666" }}
                  />
                  {tour.shipper_id}
                </li>
              ))}
            </ul>
          </div>
        )}

        {fleetResult.unassigned_order_ids.length > 0 && (
          <div className="unassigned-section">
            <h3>Đơn chưa gán được</h3>
            <ul className="stop-list">
              {fleetResult.unassigned_order_ids.map((oid) => (
                <li key={oid} className="stop-item">
                  {oid}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

FleetResultPanel.propTypes = {
  fleetResult: FleetResultPropType,
  shipperColorMap: ShipperColorMapPropType,
};