import React from "react";
import { formatDistance } from "../utils/format";

export default function FleetResultPanel({ fleetResult, shipperColorMap }) {
  if (!fleetResult) return null;

  return (
    <div className="panel-card">
      <h2>Kết quả tối ưu</h2>
      <div className="fleet-result">
        <div className="fleet-total">
          Tổng quãng đường đội: {formatDistance(fleetResult.total_distance_meters)}
        </div>

        {fleetResult.tours.map((tour) => (
          <div key={tour.shipper_id} className="shipper-tour">
            <div className="shipper-tour-header">
              <span
                className="shipper-color-dot"
                style={{ background: shipperColorMap[tour.shipper_id] || "#666" }}
              />
              <span className="shipper-name">{tour.shipper_id}</span>
              <span className="shipper-distance">
                {formatDistance(tour.total_distance_meters)}
              </span>
            </div>
            <ul className="stop-list">
              {tour.ordered_stops.map((stop, i) => (
                <li key={i} className="stop-item">
                  <span className={`stop-badge ${stop.kind}`}>
                    {stop.kind === "pickup" ? "Lấy" : "Giao"}
                  </span>
                  <span>{stop.order_id}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}

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
