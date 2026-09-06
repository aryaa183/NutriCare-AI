import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ApiErrorBody, TokenResponse } from "./types";

// Vite env var — set VITE_API_BASE_URL in .env if your backend isn't on
// localhost:8000 (see .env.example).
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const ACCESS_KEY = "nutricare.access_token";
const REFRESH_KEY = "nutricare.refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (tokens: TokenResponse) => {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// The backend's JWT refresh flow issues a refresh token at login, but v1 has
// no POST /auth/refresh endpoint yet (see README — logout is a documented
// no-op for the same stateless-JWT reason). So on a 401 we can't silently
// mint a new access token; the cleanest honest behavior is to sign the user
// out and let them log back in, rather than pretending to refresh.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
      if (location.pathname !== "/login") {
        location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

export function extractErrorMessage(error: unknown, fallback = "Something went wrong."): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined;
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail) && body.detail.length > 0) return body.detail[0].msg;
    if (error.message) return error.message;
  }
  return fallback;
}
