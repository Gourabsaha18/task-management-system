
import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("taskflow_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export function errorText(error) {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }

  if (detail) return detail;

  if (error?.code === "ERR_NETWORK") {
    return "Cannot reach FastAPI. Check the API URL and backend CORS settings.";
  }

  return error?.message || "Something went wrong";
}

export async function login(email, password) {
  const body = new URLSearchParams({
    username: email,
    password,
  });

  const { data } = await api.post("/auth/login", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  localStorage.setItem("taskflow_token", data.access_token);

  return data;
}

export async function register(username, email, password) {
  const { data } = await api.post("/auth/register", {
    username,
    email,
    password,
  });

  return data;
}

export async function getTasks() {
  const { data } = await api.get("/tasks/");

  return Array.isArray(data) ? data : data.items || [];
}

export async function addTask(payload) {
  const { data } = await api.post("/tasks/", payload);

  return data;
}

export async function editTask(id, payload) {
  const { data } = await api.patch(`/tasks/${id}`, payload);

  return data;
}

export async function removeTask(id) {
  return api.delete(`/tasks/${id}`);
}
