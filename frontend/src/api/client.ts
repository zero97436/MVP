import axios from "axios";

const TOKEN_KEY = "sh_token";

export const api = axios.create({
  baseURL: "/api",
});

// Injecte le JWT dans chaque requête.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Déconnexion automatique sur 401.
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};
