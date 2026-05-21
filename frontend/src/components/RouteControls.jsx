import React from "react";
import { SELECTION_MODES } from "../hooks/useRoutePoints";

const MODE_LABELS = {
  [SELECTION_MODES.START]: "Set Start A",
  [SELECTION_MODES.END]: "Set End B",
  [SELECTION_MODES.WAYPOINT]: "Add Waypoint",
};

export default function RouteControls({
  selectionMode,
  onSelectionModeChange,
  startPoint,
  endPoint,
  selectedPoints,
  onOptimize,
  onClear,
  isOptimizing,
}) {
  const canOptimize = Boolean(startPoint && endPoint);

  return (
    <div className="panel-card controls-card">
      <h2>Điều khiển</h2>

      <div className="mode-button-group" aria-label="Route point selection mode">
        {Object.values(SELECTION_MODES).map((mode) => (
          <button
            key={mode}
            className={selectionMode === mode ? "mode-button active" : "mode-button"}
            onClick={() => onSelectionModeChange(mode)}
            type="button"
          >
            {MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      <p className="helper-text">Mode hiện tại: <strong>{MODE_LABELS[selectionMode]}</strong>. Chọn mode rồi click trên map.</p>

      <button className="primary-button" onClick={onOptimize} disabled={!canOptimize || isOptimizing}>
        {isOptimizing ? "Đang tối ưu..." : "Optimize Route A → B"}
      </button>
      <button className="secondary-button" onClick={onClear} disabled={selectedPoints.length === 0 || isOptimizing}>
        Clear
      </button>
      <p className="helper-text">
        {canOptimize ? "Đã có Start và End, có thể tìm route." : "Cần chọn đủ Start A và End B để tìm route."}
      </p>
    </div>
  );
}
