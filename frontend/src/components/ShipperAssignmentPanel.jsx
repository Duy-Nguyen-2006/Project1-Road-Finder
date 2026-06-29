import React from "react";
import PropTypes from "prop-types";
import { VRP_STATUS } from "../hooks/useVrpState";
import {
  getOrderDisplayColor,
  getOrderLabel,
  getPickupGlyph,
  getDropoffGlyph,
} from "../utils/orders";
import { getShipperGlyph, getShipperLabel } from "../utils/shippers";
import {
  OrderAssignmentsPropType,
  OrderPropType,
  ShipperColorMapPropType,
  ShipperPropType,
} from "./proptypes";

export default function ShipperAssignmentPanel({
  shippers,
  orders,
  selectedShipperId,
  selectedOrderIds,
  orderAssignments,
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
        Chọn shipper, tick các đơn shipper đó nhận. Đơn đã gán cho shipper khác
        sẽ bị khóa.
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
      {!selectedShipperId ? (
        <p className="helper-text">Chọn shipper trước khi tick đơn.</p>
      ) : orders.length === 0 ? (
        <p className="helper-text">Chưa có đơn hàng. Thêm đơn trên bản đồ.</p>
      ) : (
        <div className="order-select-list">
          {orders.map((order) => {
            const label = getOrderLabel(order.id);
            const owner = orderAssignments[order.id];
            const checked = owner === selectedShipperId;
            const lockedByOther = Boolean(owner && owner !== selectedShipperId);
            const ownerColor = lockedByOther
              ? shipperColorMap?.[owner] ?? "#666"
              : undefined;

            return (
              <label
                key={order.id}
                className={`select-row order-select-row${checked ? " selected" : ""}${lockedByOther ? " locked" : ""}`}
                style={{
                  borderColor: checked
                    ? shipperColorMap?.[selectedShipperId]
                    : lockedByOther
                      ? ownerColor
                      : undefined,
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={lockedByOther}
                  onChange={() => onToggleOrder(order.id)}
                />
                <span
                  className="order-color-dot"
                  style={{
                    background: getOrderDisplayColor(
                      order.id,
                      orders,
                      orderAssignments,
                      shipperColorMap
                    ),
                  }}
                />
                <span className="select-row-label">
                  <strong>{label}</strong>
                  <span className="order-route-hint">
                    {getPickupGlyph(order.id)} (lấy) → {getDropoffGlyph(order.id)} (giao)
                  </span>
                  {lockedByOther ? (
                    <span
                      className="owner-badge"
                      style={{
                        color: ownerColor,
                        borderColor: ownerColor,
                        background: `${ownerColor}18`,
                      }}
                    >
                      Đã gán {getShipperGlyph(owner)}
                    </span>
                  ) : null}
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
        {status === VRP_STATUS.LOADING
          ? "Đang tối ưu..."
          : "Tối ưu tất cả shipper"}
      </button>
    </div>
  );
}

ShipperAssignmentPanel.propTypes = {
  shippers: PropTypes.arrayOf(ShipperPropType).isRequired,
  orders: PropTypes.arrayOf(OrderPropType).isRequired,
  selectedShipperId: PropTypes.string,
  selectedOrderIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  orderAssignments: OrderAssignmentsPropType.isRequired,
  shipperColorMap: ShipperColorMapPropType,
  status: PropTypes.string.isRequired,
  canOptimize: PropTypes.bool.isRequired,
  onSelectShipper: PropTypes.func.isRequired,
  onToggleOrder: PropTypes.func.isRequired,
  onOptimize: PropTypes.func.isRequired,
};