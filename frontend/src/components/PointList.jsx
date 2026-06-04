import React from "react";
import { SELECTION_MODES } from "../hooks/useRoutePoints";

function PointDetails({ point }) {
  if (!point) {
    return <p className="empty-text">Chưa chọn.</p>;
  }
  return (
    <div className="point-coords">
      Lat: {point.latitude.toFixed(6)}, Lng: {point.longitude.toFixed(6)}
    </div>
  );
}

export default function PointList({ startPoint, endPoint, onRemovePoint }) {
  return (
    <div className="panel-card">
      <h2>Điểm Start / End</h2>

      <div className="point-section point-section-start">
        <div>
          <strong>Start</strong>
          <PointDetails point={startPoint} />
        </div>
        {startPoint ? (
          <button
            className="icon-button"
            onClick={() => onRemovePoint(SELECTION_MODES.START)}
            type="button"
          >
            Xóa
          </button>
        ) : null}
      </div>

      <div className="point-section point-section-end">
        <div>
          <strong>End</strong>
          <PointDetails point={endPoint} />
        </div>
        {endPoint ? (
          <button
            className="icon-button"
            onClick={() => onRemovePoint(SELECTION_MODES.END)}
            type="button"
          >
            Xóa
          </button>
        ) : null}
      </div>
    </div>
  );
}
