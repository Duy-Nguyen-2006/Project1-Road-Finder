/**
 * Build per-shipper stop sequences (1, 2, 3…) from tour results.
 * Returns lookup keys `${orderId}:${kind}` scoped per shipper via nested map.
 */
export function buildTourDisplayData(tourResults = []) {
  const stopLookup = {};
  const shipperTours = [];

  for (const tour of tourResults) {
    let sequence = 1;
    const stops = tour.ordered_stops.map((stop) => {
      const entry = { ...stop, sequence };
      stopLookup[`${tour.shipper_id}:${stop.order_id}:${stop.kind}`] = sequence;
      sequence += 1;
      return entry;
    });
    shipperTours.push({ ...tour, stops });
  }

  const totalDistanceMeters = tourResults.reduce(
    (sum, tour) => sum + (tour.total_distance_meters ?? 0),
    0
  );

  return { stopLookup, shipperTours, totalDistanceMeters };
}