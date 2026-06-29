export function getShipperNumber(shipperId) {
  const match = shipperId.match(/\d+/);
  return match ? Number.parseInt(match[0], 10) : 0;
}

export function getShipperGlyph(shipperId) {
  const n = getShipperNumber(shipperId);
  return n > 0 ? `S${n}` : "S";
}

export function getShipperLabel(shipperId) {
  const n = getShipperNumber(shipperId);
  return n > 0 ? `Shipper ${n}` : shipperId;
}

export function getShipperShortLabel(shipperId) {
  return getShipperGlyph(shipperId);
}