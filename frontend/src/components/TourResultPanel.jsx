import React from "react";
import PropTypes from "prop-types";
import { formatDistance } from "../utils/format";
import {
  getDropoffGlyph,
  getOrderColor,
  getOrderLabel,
  getPickupGlyph,
} from "../utils/orders";
import { getShipperGlyph, getShipperLabel } from "../utils/shippers";
import {
  OrderPropType,
  ShipperColorMapPropType,
  TourResultPropType,
} from "./proptypes";

export default function TourResultPanel({
  tourResult,
  orders,
  shipperColorMap,
}) {
  if (!tourResult) return null;

  const shipperColor = shipperColorMap?.[tourResult.shipper_id] ?? "#2563eb";

  return (
    <div className="panel-card">
      <h2>Kết quả tuyến</h2>
      <div className="tour-result">
        <div className="tour-result-header">
          <span
            className="shipper-color-dot"
            style={{ background: shipperColor }}
          />
          <span className="shipper-name">
            {getShipperLabel(tourResult.shipper_id)} ({getShipperGlyph(tourResult.shipper_id)})
          </span>
        </div>

        <div className="tour-distance-hero">
          <span className="tour-distance-label">Quãng đường</span>
          <span className="tour-distance-value">
            {formatDistance(tourResult.total_distance_meters)}
          </span>
        </div>

        <h3>Thứ tự đi</h3>
        <ul className="stop-list">
          <li className="stop-item">
            <span className="stop-badge shipper">Xuất phát</span>
            <span>
              {getShipperLabel(tourResult.shipper_id)} ({getShipperGlyph(tourResult.shipper_id)})
            </span>
          </li>
          {tourResult.ordered_stops.map((stop) => {
            const color = getOrderColor(stop.order_id, orders);
            const label = getOrderLabel(stop.order_id);
            const glyph =
              stop.kind === "pickup"
                ? getPickupGlyph(stop.order_id)
                : getDropoffGlyph(stop.order_id);
            return (
              <li
                key={`${stop.order_id}-${stop.kind}`}
                className="stop-item"
              >
                <span
                  className="stop-badge order-stop"
                  style={{ background: `${color}22`, color, borderColor: color }}
                >
                  {glyph}
                </span>
                <span>
                  {label} — {stop.kind === "pickup" ? "lấy hàng" : "giao hàng"}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

TourResultPanel.propTypes = {
  tourResult: TourResultPropType,
  orders: PropTypes.arrayOf(OrderPropType).isRequired,
  shipperColorMap: ShipperColorMapPropType,
};