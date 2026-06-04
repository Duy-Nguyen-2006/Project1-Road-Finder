import React from "react";
import { SELECTION_MODES, ROUTE_STATUS } from "../hooks/useRoutePoints";

const MODE_LABELS = {
  [SELECTION_MODES.START]: "Start",
  [SELECTION_MODES.END]: "End",
};

export default function RouteControls({
  selectionMode,
  onSelectionModeChange,
  startPoint,
  endPoint,
  status,
  boundsLoaded,
  onFindRoute,
  onClear,
}) {
  const canFind =
    Boolean(startPoint && endPoint) &&
    boundsLoaded &&
    status !== ROUTE_STATUS.LOADING;

  const isLoading = status === ROUTE_STATUS.LOADING;

  return (
    <div className="panel-card controls-card">
      <h2>Điều khiển</h2>

      <div className="mode-button-group" aria-label="Chế độ chọn điểm">
        {Object.values(SELECTION_MODES).map((mode) => (
          <button
            key={mode}
            className={
              selectionMode === mode ? "mode-button active" : "mode-button"
            }
            onClick={() => onSelectionModeChange(mode)}
            type="button"
          >
            {MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      <p className="helper-text">
        Đang chọn: <strong>{MODE_LABELS[selectionMode]}</strong>. Click lên map
        trong vùng bbox đỏ để đặt điểm.
      </p>

      <button
        className="primary-button"
        onClick={onFindRoute}
        disabled={!canFind}
        type="button"
      >
        {isLoading ? "Đang tìm đường..." : "Find Shortest Path"}
      </button>
      <button
        className="secondary-button"
        onClick={onClear}
        disabled={!startPoint && !endPoint}
        type="button"
      >
        Clear
      </button>

      {!boundsLoaded ? (
        <p className="error-text">Đang tải vùng hỗ trợ từ backend...</p>
      ) : !canFind ? (
        <p className="helper-text">Cần chọn Start và End trong vùng bbox đỏ.</p>
      ) : null}
    </div>
  );
}
