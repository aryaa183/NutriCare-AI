import { create } from "zustand";
import * as endpoints from "../api/endpoints";
import type { HealthProfileResponse } from "../api/types";

interface ProfileState {
  profile: HealthProfileResponse | null;
  status: "idle" | "loading" | "loaded" | "missing" | "error";
  fetch: () => Promise<void>;
  set: (profile: HealthProfileResponse) => void;
  clear: () => void;
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  status: "idle",

  fetch: async () => {
    set({ status: "loading" });
    try {
      const profile = await endpoints.getProfile();
      set({ profile, status: "loaded" });
    } catch (err: unknown) {
      const isAxios404 =
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        (err as { response?: { status?: number } }).response?.status === 404;
      set({ status: isAxios404 ? "missing" : "error", profile: null });
    }
  },

  set: (profile) => set({ profile, status: "loaded" }),

  clear: () => set({ profile: null, status: "idle" }),
}));
