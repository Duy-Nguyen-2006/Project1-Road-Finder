export const ORDER_COLORS = [
  "#7c3aed",
  "#ea580c",
  "#059669",
  "#db2777",
  "#0284c7",
  "#ca8a04",
  "#be123c",
  "#0d9488",
];

export function getOrderNumber(orderId) {
  const match = orderId.match(/\d+/);
  return match ? Number.parseInt(match[0], 10) : 0;
}

export function getOrderLabel(orderId) {
  const n = getOrderNumber(orderId);
  return n > 0 ? `Đơn ${n}` : orderId;
}

export function getOrderColor(orderId, orders) {
  const index = orders.findIndex((o) => o.id === orderId);
  return ORDER_COLORS[index >= 0 ? index % ORDER_COLORS.length : 0];
}

export function getPickupGlyph(orderId) {
  const n = getOrderNumber(orderId);
  return n > 0 ? `P${n}` : "P";
}

export function getDropoffGlyph(orderId) {
  const n = getOrderNumber(orderId);
  return n > 0 ? `D${n}` : "D";
}

export function buildOrderColorMap(orders) {
  const map = {};
  orders.forEach((order, index) => {
    map[order.id] = ORDER_COLORS[index % ORDER_COLORS.length];
  });
  return map;
}

/** Màu hiển thị đơn: palette riêng khi chưa gán, màu shipper khi đã gán. */
export function getOrderDisplayColor(
  orderId,
  orders,
  orderAssignments = {},
  shipperColorMap = {}
) {
  const owner = orderAssignments[orderId];
  if (owner) {
    return shipperColorMap[owner] ?? getOrderColor(orderId, orders);
  }
  return getOrderColor(orderId, orders);
}