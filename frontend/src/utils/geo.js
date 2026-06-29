export function isInsideBbox(point, bbox) {
  if (!point || !bbox) return false;
  const { latitude, longitude } = point;
  const { min_latitude, min_longitude, max_latitude, max_longitude } = bbox;
  return (
    latitude >= min_latitude &&
    latitude <= max_latitude &&
    longitude >= min_longitude &&
    longitude <= max_longitude
  );
}

export function bboxToLeaflet(bbox) {
  if (!bbox) return null;
  return [
    [bbox.min_latitude, bbox.min_longitude],
    [bbox.max_latitude, bbox.max_longitude],
  ];
}

export function routePointsToLeaflet(routePoints) {
  if (!Array.isArray(routePoints)) return [];
  return routePoints.map((p) => [p.latitude, p.longitude]);
}

// Haversine distance in meters between two {latitude, longitude} points.
const EARTH_RADIUS_METERS = 6_371_000;

function toRadians(degrees) {
  return (degrees * Math.PI) / 180;
}

export function haversineMeters(a, b) {
  if (!a || !b) return Number.POSITIVE_INFINITY;
  const dLat = toRadians(b.latitude - a.latitude);
  const dLng = toRadians(b.longitude - a.longitude);
  const lat1 = toRadians(a.latitude);
  const lat2 = toRadians(b.latitude);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  return EARTH_RADIUS_METERS * c;
}

// Returns the distance (meters) from `point` to the nearest entry in `nodes`.
// `nodes` is an array of {id, latitude, longitude}.
export function distanceToNearestNodeMeters(point, nodes) {
  if (!point || !Array.isArray(nodes) || nodes.length === 0) {
    return Number.POSITIVE_INFINITY;
  }
  let best = Number.POSITIVE_INFINITY;
  for (const n of nodes) {
    const d = haversineMeters(point, n);
    if (d < best) best = d;
  }
  return best;
}
