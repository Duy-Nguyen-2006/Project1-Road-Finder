const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function optimizeRoute(points) {
  const response = await fetch(`${API_BASE_URL}/optimize-route`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ points }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Không thể tối ưu route");
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

export async function fetchIntersections(cityName = "Ho Chi Minh City", bbox = null) {
  const params = new URLSearchParams({ city_name: cityName });
  if (bbox) {
    params.append('bbox', bbox);
  }
  
  const response = await fetch(`${API_BASE_URL}/intersections?${params.toString()}`);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Không thể lấy dữ liệu giao lộ");
  }
  
  return response.json();
}
