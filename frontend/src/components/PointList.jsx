import React from "react";
import { SELECTION_MODES } from "../hooks/useRoutePoints";

function PointDetails({ point }) {
  if (!point) {
    return <p className="empty-text">Chưa chọn.</p>;
  }

  return (
    <div className="point-coords">
      Lat: {point.lat.toFixed(6)}, Lng: {point.lng.toFixed(6)}
    </div>
  );
}

export default function PointList({ startPoint, endPoint, waypoints, onRemovePoint }) {
  return (
    <div className="panel-card">
      <h2>Route A → B</h2>

      <div className="point-section point-section-start">
        <div>
          <strong>Start A</strong>
          <PointDetails point={startPoint} />
        </div>
        {startPoint ? (
          <button className="icon-button" onClick={() => onRemovePoint(SELECTION_MODES.START)}>
            Xóa
          </button>
        ) : null}
      </div>

      <div className="point-section point-section-end">
        <div>
          <strong>End B</strong>
          <PointDetails point={endPoint} />
        </div>
        {endPoint ? (
          <button className="icon-button" onClick={() => onRemovePoint(SELECTION_MODES.END)}>
            Xóa
          </button>
        ) : null}
      </div>

      <h3>Waypoints</h3>
      {waypoints.length === 0 ? (
        <p className="empty-text">Chưa có waypoint trung gian.</p>
      ) : (
        <ul className="point-list">
          {waypoints.map((point, index) => (
            <li key={`${point.lat}-${point.lng}-${index}`} className="point-item">
              <div>
                <strong>Waypoint {index + 1}</strong>
                <PointDetails point={point} />
              </div>
              <button className="icon-button" onClick={() => onRemovePoint(SELECTION_MODES.WAYPOINT, index)}>
                Xóa
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
