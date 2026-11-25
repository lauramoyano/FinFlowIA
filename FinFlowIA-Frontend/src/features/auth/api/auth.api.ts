import apiClient from "@/shared/lib/api-client";
import type { ApiResponse } from "@/shared/types/api.types";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "@/features/auth/types/auth.types";

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<ApiResponse<TokenResponse>>(
      "/auth/login",
      data,
    );
    return response.data.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<ApiResponse<User>>(
      "/auth/register",
      data,
    );
    return response.data.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<ApiResponse<User>>("/auth/me");
    return response.data.data;
  },
};
