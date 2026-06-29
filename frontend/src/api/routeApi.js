export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "http://localhost:8000" : "");

const ACCEPTED_AREA_DETAIL = "Error: Not in accepted area";

// Network/CORS/backend-down errors surface as TypeError("Failed to fetch").
// Wrap with a friendlier message that points the user to the backend URL.
function networkErrorMessage(cause) {
  return `Không kết nối được backend tại ${API_BASE_URL}. Hãy chắc chắn backend đang chạy (uvicorn app.main:app --port 8000) và CORS cho phép origin này. (${cause?.message ?? cause})`;
}

async function parseError(response) {
  const body = await parseJsonBody(response);
  if (typeof body?.detail === "string") {
    return body.detail;
  }
  if (body?.detail) {
    return JSON.stringify(body.detail);
  }
  return (await response.text()) || "Lỗi không xác định từ backend";
}

async function parseJsonBody(response) {
  const text = await response.clone().text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function postJson(url, data) {
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

async function getJson(url) {
  let response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getGraphBounds() {
  return getJson(`${API_BASE_URL}/graph/bounds`);
}

export async function postRoute({ start, end, options }) {
  return postJson(`${API_BASE_URL}/route`, { start, end, options });
}

export async function postAssignments({ order, shippers, options }) {
  return postJson(`${API_BASE_URL}/assignments`, { order, shippers, options });
}

export async function postTours({ shipper, orders, options }) {
  return postJson(`${API_BASE_URL}/tours`, { shipper, orders, options });
}

export async function postFleet({ shippers, orders, options }) {
  return postJson(`${API_BASE_URL}/fleet`, { shippers, orders, options });
}

export async function checkHealth() {
  return getJson(`${API_BASE_URL}/health`);
}

export const ERROR_MESSAGES = {
  ACCEPTED_AREA: ACCEPTED_AREA_DETAIL,
};

export { ACCEPTED_AREA_DETAIL };
