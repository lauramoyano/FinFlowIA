import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, TokenResponse } from "@/features/auth/types/auth.types";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  setAuth: (user: User, tokenResponse: TokenResponse) => void;
  setUser: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,

      setAuth: (user, tokenResponse) =>
        set({ user, token: tokenResponse.access_token, isLoading: false }),

      setUser: (user) => set({ user }),

      logout: () => set({ user: null, token: null }),

      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: "finflowia-auth",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    },
  ),
);
