const API_URL = "http://localhost:8000";

export const apiRequest = async (endpoint, method = "GET", body = null, isForm = false) => {
  const token = localStorage.getItem("token");

  let headers = {};

  if (!isForm) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : null,
  });

  const data = await response.json();

  if (!response.ok) {
    console.error(data);
    throw new Error(data.detail || "Error en la petición");
  }

  return data;
};