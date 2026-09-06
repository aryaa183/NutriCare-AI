import { create } from "zustand";
import { tokenStorage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { LoginRequest, SignupRequest } from "../api/types";

interface AuthState {
  isAuthenticated: boolean;
  isBusy: boolean;
  signup: (payload: SignupRequest) => Promise<void>;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: Boolean(tokenStorage.getAccess()),
  isBusy: false,

  signup: async (payload) => {
    set({ isBusy: true });
    try {
      await endpoints.signup(payload);
      const tokens = await endpoints.login({ email: payload.email, password: payload.password });
      tokenStorage.set(tokens);
      set({ isAuthenticated: true });
    } finally {
      set({ isBusy: false });
    }
  },

  login: async (payload) => {
    set({ isBusy: true });
    try {
      const tokens = await endpoints.login(payload);
      tokenStorage.set(tokens);
      set({ isAuthenticated: true });
    } finally {
      set({ isBusy: false });
    }
  },

  logout: async () => {
    // Await so the Authorization header is attached before we clear the
    // token — axios request interceptors run as a microtask, so clearing
    // synchronously beforehand loses the race and the request goes out
    // unauthenticated.
    await endpoints.logout().catch(() => {});
    tokenStorage.clear();
    set({ isAuthenticated: false });
  },
}));
