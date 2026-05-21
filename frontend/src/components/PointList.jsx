export default function PointList({ selectedPoints, onRemovePoint }) {
  return (
    <div className="panel-card">
      <h2>Điểm đã chọn</h2>
      {selectedPoints.length === 0 ? (
        <p className="empty-text">Chưa có điểm nào được chọn.</p>
      ) : (
        <ul className="point-list">
          {selectedPoints.map((point, index) => (
            <li key={`${point.lat}-${point.lng}-${index}`} className="point-item">
              <div>
                <strong>Point {index + 1}</strong>
                <div className="point-coords">
                  Lat: {point.lat.toFixed(6)}, Lng: {point.lng.toFixed(6)}
                </div>
              </div>
              <button className="icon-button" onClick={() => onRemovePoint(index)}>
                Xóa
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
