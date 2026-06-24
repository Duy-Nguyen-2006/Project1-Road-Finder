import PropTypes from "prop-types";

export const CoordPropType = PropTypes.shape({
  latitude: PropTypes.number.isRequired,
  longitude: PropTypes.number.isRequired,
});

export const OrderPropType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  pickup: CoordPropType.isRequired,
  dropoff: CoordPropType.isRequired,
});

export const ShipperPropType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  location: CoordPropType.isRequired,
});

export const TourStopPropType = PropTypes.shape({
  order_id: PropTypes.string.isRequired,
  kind: PropTypes.string.isRequired,
  node_id: PropTypes.string.isRequired,
});

export const TourPropType = PropTypes.shape({
  shipper_id: PropTypes.string.isRequired,
  ordered_stops: PropTypes.arrayOf(TourStopPropType).isRequired,
  total_distance_meters: PropTypes.number.isRequired,
});

export const FleetResultPropType = PropTypes.shape({
  total_distance_meters: PropTypes.number.isRequired,
  tours: PropTypes.arrayOf(TourPropType),
  unassigned_order_ids: PropTypes.arrayOf(PropTypes.string),
});

export const ShipperColorMapPropType = PropTypes.objectOf(PropTypes.string);
