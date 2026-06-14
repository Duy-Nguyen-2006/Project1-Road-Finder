import React from "react";

function CoordDisplay({ point }) {
  if (!point) return null;
  return (
    <div className="point-coords">
      {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
    </div>
  );
}

export default function PointList({
  orders,
  shippers,
  shipperColorMap,
  onRemoveOrder,
  onRemoveShipper,
}) {
  const hasContent = orders.length > 0 || shippers.length > 0;

  return (
    <div className="panel-card">
      <h2>Điểm đã chọn</h2>

      {!hasContent && <p className="empty-text">Chưa có điểm nào.</p>}

      {shippers.length > 0 && (
        <>
          <h3>Shipper ({shippers.length})</h3>
          {shippers.map((s) => (
            <div key={s.id} className="point-section">
              <div>
                <strong style={{ color: shipperColorMap[s.id] || "#333" }}>
                  {s.id}
                </strong>
                <CoordDisplay point={s.location} />
              </div>
              <button
                className="icon-button"
                onClick={() => onRemoveShipper(s.id)}
                type="button"
              >
                Xóa
              </button>
            </div>
          ))}
        </>
      )}

      {orders.length > 0 && (
        <>
          <h3>Đơn hàng ({orders.length})</h3>
          {orders.map((o) => (
            <div key={o.id} className="point-section">
              <div>
                <strong>{o.id}</strong>
                <div className="point-coords">
                  <span className="stop-badge pickup">Lấy</span>{" "}
                  {o.pickup.latitude.toFixed(6)}, {o.pickup.longitude.toFixed(6)}
                </div>
                <div className="point-coords">
                  <span className="stop-badge dropoff">Giao</span>{" "}
                  {o.dropoff.latitude.toFixed(6)}, {o.dropoff.longitude.toFixed(6)}
                </div>
              </div>
              <button
                className="icon-button"
                onClick={() => onRemoveOrder(o.id)}
                type="button"
              >
                Xóa
              </button>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
