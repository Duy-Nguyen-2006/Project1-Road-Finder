export function formatDistance(meters) {
  if (typeof meters !== "number" || !Number.isFinite(meters) || meters < 0) {
    return "—";
  }
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(2)} km`;
}
