export default function RouteControls({ selectedPoints, onOptimize, onClear, isOptimizing }) {
  const canOptimize = selectedPoints.length >= 2;

  return (
    <div className="panel-card controls-card">
      <h2>Điều khiển</h2>
      <button className="primary-button" onClick={onOptimize} disabled={!canOptimize || isOptimizing}>
        {isOptimizing ? "Đang tối ưu..." : "Optimize Route"}
      </button>
      <button className="secondary-button" onClick={onClear} disabled={selectedPoints.length === 0 || isOptimizing}>
        Clear
      </button>
      <p className="helper-text">
        {canOptimize ? "Sẵn sàng tối ưu lộ trình." : "Cần ít nhất 2 điểm để tối ưu."}
      </p>
    </div>
  );
}
