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
