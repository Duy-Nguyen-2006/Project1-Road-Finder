import React, { useMemo } from "react";
import PropTypes from "prop-types";
import { formatDistance } from "../utils/format";
import {
  getDropoffGlyph,
  getOrderLabel,
  getPickupGlyph,
} from "../utils/orders";
import { getShipperGlyph, getShipperLabel } from "../utils/shippers";
import { buildTourDisplayData } from "../utils/tourDisplay";
import {
  OrderPropType,
  ShipperColorMapPropType,
  TourResultsPropType,
} from "./proptypes";

export default function MultiShipperResultPanel({
  tourResults,
  orders,
  shipperColorMap,
}) {
  const { shipperTours, totalDistanceMeters } = useMemo(
    () => buildTourDisplayData(tourResults),
    [tourResults]
  );

  if (!tourResults?.length) return null;

  return (
    <div className="panel-card">
      <h2>Kết quả tuyến</h2>
      <div className="multi-tour-result">
        <div className="fleet-total">
          Tổng quãng đường đội: {formatDistance(totalDistanceMeters)}
        </div>

        {shipperTours.map((tour) => {
          const shipperColor =
            shipperColorMap?.[tour.shipper_id] ?? "#2563eb";
          return (
            <div key={tour.shipper_id} className="shipper-tour">
              <div className="shipper-tour-header">
                <span
                  className="shipper-color-dot"
                  style={{ background: shipperColor }}
                />
                <span className="shipper-name">
                  {getShipperLabel(tour.shipper_id)} (
                  {getShipperGlyph(tour.shipper_id)})
                </span>
                <span className="shipper-distance">
                  {formatDistance(tour.total_distance_meters)}
                </span>
              </div>

              <ul className="stop-list">
                <li className="stop-item">
                  <span
                    className="stop-badge shipper"
                    style={{
                      background: `${shipperColor}22`,
                      color: shipperColor,
                      borderColor: shipperColor,
                    }}
                  >
                    ▶
                  </span>
                  <span>
                    Xuất phát — {getShipperLabel(tour.shipper_id)} (
                    {getShipperGlyph(tour.shipper_id)})
                  </span>
                </li>
                {tour.stops.map((stop) => {
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
                        style={{
                          background: `${shipperColor}22`,
                          color: shipperColor,
                          borderColor: shipperColor,
                        }}
                      >
                        {stop.sequence}
                      </span>
                      <span>
                        {label} — {glyph}{" "}
                        {stop.kind === "pickup" ? "lấy hàng" : "giao hàng"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}

MultiShipperResultPanel.propTypes = {
  tourResults: TourResultsPropType,
  orders: PropTypes.arrayOf(OrderPropType).isRequired,
  shipperColorMap: ShipperColorMapPropType,
};