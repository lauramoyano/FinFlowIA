import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/features/auth/api/auth.api";
import { useAuthStore } from "@/features/auth/store/auth.store";
import type { LoginRequest, RegisterRequest } from "@/features/auth/types/auth.types";

export function useLogin() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const tokenResponse = await authApi.login(data);
      // Store the token before fetching the profile so the api-client
      // interceptor has it available to attach as the Authorization header.
      useAuthStore.setState({ token: tokenResponse.access_token });
      const user = await authApi.getMe();
      return { tokenResponse, user };
    },
    onSuccess: ({ tokenResponse, user }) => {
      setAuth(user, tokenResponse);
      navigate("/home");
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: () => {
      navigate("/login");
    },
  });
}

export function useLogout() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();

  return () => {
    logout();
    navigate("/login");
  };
}

export function useCurrentUser() {
  const { token } = useAuthStore();

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.getMe,
    enabled: !!token,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
