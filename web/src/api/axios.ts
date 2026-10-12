import axios from "axios";

export const TOKEN_KEY = "jwt_token";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Auto attach token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);

  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
});
