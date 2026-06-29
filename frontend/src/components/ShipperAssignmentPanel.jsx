import React from "react";
import PropTypes from "prop-types";
import { VRP_STATUS } from "../hooks/useVrpState";
import {
  getOrderColor,
  getOrderLabel,
  getOrderNumber,
} from "../utils/orders";
import { getShipperGlyph, getShipperLabel } from "../utils/shippers";
import {
  OrderPropType,
  ShipperColorMapPropType,
  ShipperPropType,
} from "./proptypes";

export default function ShipperAssignmentPanel({
  shippers,
  orders,
  selectedShipperId,
  selectedOrderIds,
  shipperColorMap,
  status,
  canOptimize,
  onSelectShipper,
  onToggleOrder,
  onOptimize,
}) {
  if (shippers.length === 0) {
    return (
      <div className="panel-card">
        <h2>Phân công & tối ưu</h2>
        <p className="helper-text">Thêm ít nhất một shipper trên bản đồ trước.</p>
      </div>
    );
  }

  return (
    <div className="panel-card assignment-panel">
      <h2>Phân công & tối ưu</h2>
      <p className="helper-text">
        Chọn shipper, tick các đơn shipper đó nhận, rồi bấm tối ưu quãng đường.
      </p>

      <h3>1. Chọn shipper</h3>
      <div className="shipper-select-list">
        {shippers.map((shipper) => (
          <label key={shipper.id} className="select-row">
            <input
              type="radio"
              name="selected-shipper"
              checked={selectedShipperId === shipper.id}
              onChange={() => onSelectShipper(shipper.id)}
            />
            <span
              className="shipper-color-dot"
              style={{ background: shipperColorMap?.[shipper.id] ?? "#666" }}
            />
            <span className="select-row-label">
              <strong>{getShipperLabel(shipper.id)}</strong>
              <span className="order-route-hint">{getShipperGlyph(shipper.id)}</span>
            </span>
          </label>
        ))}
      </div>

      <h3>2. Chọn đơn shipper nhận</h3>
      {orders.length === 0 ? (
        <p className="helper-text">Chưa có đơn hàng. Thêm đơn trên bản đồ.</p>
      ) : (
        <div className="order-select-list">
          {orders.map((order) => {
            const color = getOrderColor(order.id, orders);
            const label = getOrderLabel(order.id);
            const n = getOrderNumber(order.id);
            const checked = selectedOrderIds.includes(order.id);
            return (
              <label
                key={order.id}
                className={`select-row order-select-row${checked ? " selected" : ""}`}
                style={{ borderColor: checked ? color : undefined }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggleOrder(order.id)}
                />
                <span className="order-color-dot" style={{ background: color }} />
                <span className="select-row-label">
                  <strong>{label}</strong>
                  <span className="order-route-hint">
                    P{n} (lấy) → D{n} (giao)
                  </span>
                </span>
              </label>
            );
          })}
        </div>
      )}

      <button
        className="primary-button"
        onClick={onOptimize}
        disabled={!canOptimize}
        type="button"
      >
        {status === VRP_STATUS.LOADING ? "Đang tối ưu..." : "Tối ưu quãng đường"}
      </button>
    </div>
  );
}

ShipperAssignmentPanel.propTypes = {
  shippers: PropTypes.arrayOf(ShipperPropType).isRequired,
  orders: PropTypes.arrayOf(OrderPropType).isRequired,
  selectedShipperId: PropTypes.string,
  selectedOrderIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  shipperColorMap: ShipperColorMapPropType,
  status: PropTypes.string.isRequired,
  canOptimize: PropTypes.bool.isRequired,
  onSelectShipper: PropTypes.func.isRequired,
  onToggleOrder: PropTypes.func.isRequired,
  onOptimize: PropTypes.func.isRequired,
};