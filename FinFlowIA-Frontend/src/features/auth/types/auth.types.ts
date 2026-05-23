import type { DateTimeString, UUID } from "@/shared/types/common.types";

export interface User {
  id: UUID;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: DateTimeString;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
