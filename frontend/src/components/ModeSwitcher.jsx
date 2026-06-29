import React from "react";
import PropTypes from "prop-types";
import { PLACEMENT_MODE, ORDER_STEP } from "../hooks/useVrpState";

const MODE_LABELS = {
  [PLACEMENT_MODE.ORDER]: "Đơn hàng",
  [PLACEMENT_MODE.SHIPPER]: "Shipper",
};

const STEP_LABELS = {
  [ORDER_STEP.SET_PICKUP]: "Click lên bản đồ để chọn điểm lấy hàng.",
  [ORDER_STEP.SET_DROPOFF]: "Click lên bản đồ để chọn điểm giao hàng cho đơn vừa tạo.",
};

export default function ModeSwitcher({
  placementMode,
  onPlacementModeChange,
  orderStep,
  onCancelPendingPickup,
}) {
  return (
    <div className="panel-card">
      <h2>Chế độ đặt điểm</h2>
      <div className="mode-switcher">
        {Object.values(PLACEMENT_MODE).map((mode) => (
          <button
            key={mode}
            className={placementMode === mode ? "active" : ""}
            onClick={() => onPlacementModeChange(mode)}
            type="button"
          >
            {MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      {placementMode === PLACEMENT_MODE.ORDER && (
        <>
          <p className="helper-text">{STEP_LABELS[orderStep]}</p>
          {orderStep === ORDER_STEP.SET_DROPOFF && (
            <button
              className="secondary-button"
              onClick={onCancelPendingPickup}
              type="button"
            >
              Hủy điểm lấy hàng vừa chọn
            </button>
          )}
        </>
      )}

      {placementMode === PLACEMENT_MODE.SHIPPER && (
        <p className="helper-text">Click lên bản đồ để đặt vị trí shipper.</p>
      )}
    </div>
  );
}

ModeSwitcher.propTypes = {
  placementMode: PropTypes.oneOf(Object.values(PLACEMENT_MODE)).isRequired,
  onPlacementModeChange: PropTypes.func.isRequired,
  orderStep: PropTypes.oneOf(Object.values(ORDER_STEP)).isRequired,
  onCancelPendingPickup: PropTypes.func.isRequired,
};
