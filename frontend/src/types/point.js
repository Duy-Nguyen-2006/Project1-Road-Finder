export function toBackendPoint(point) {
  return {
    latitude: point.lat,
    longitude: point.lng,
  };
}

export function toLeafletPoint(point) {
  return {
    lat: point.latitude,
    lng: point.longitude,
  };
}
