import axios from "axios";
import { API_BASE_URL, SESSION_API_URL, REQUEST_TIMEOUT } from "../config";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
});

const sessionApi = axios.create({
  baseURL: SESSION_API_URL,
  timeout: 15000,
});

// Injeta token JWT em todas as requests autenticadas
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ctf_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redireciona para login se 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("ctf_token");
      localStorage.removeItem("ctf_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const authService = {
  register: (data) => api.post("/api/auth/register", data),
  login: (username, password) => {
    const form = new FormData();
    form.append("username", username);
    form.append("password", password);
    return api.post("/api/auth/login", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  logout: () => api.post("/api/auth/logout"),
};

export const sessionService = {
  getStatus: () => api.get("/api/session/status"),
  start: () => api.post("/api/session/start"),
};

export const flagService = {
  submit: (flagNumber, flagValue) =>
    api.post("/api/flags/submit", { flag_number: flagNumber, flag_value: flagValue }),
};
