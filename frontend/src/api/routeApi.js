const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ACCEPTED_AREA_DETAIL = "Error: Not in accepted area";

async function parseError(response) {
  let message = "Lỗi không xác định từ backend";
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") {
      message = body.detail;
    } else if (body && body.detail) {
      message = JSON.stringify(body.detail);
    }
  } catch (_err) {
    try {
      message = await response.text();
    } catch (_err2) {
      // ignore
    }
  }
  return message;
}

export async function getGraphBounds() {
  const response = await fetch(`${API_BASE_URL}/graph-bounds`);
  if (!response.ok) {
    throw new Error(
      (await parseError(response)) || "Không tải được vùng hỗ trợ từ backend"
    );
  }
  return response.json();
}

export async function findShortestPath({ start, end }) {
  const response = await fetch(`${API_BASE_URL}/shortest-path`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start, end }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error("Backend health check failed");
  }
  return response.json();
}

export const ERROR_MESSAGES = {
  ACCEPTED_AREA: ACCEPTED_AREA_DETAIL,
};
