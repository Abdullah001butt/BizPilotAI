import { apiClient } from "@/lib/api/client";
import type { TokenPair, User } from "@/types/auth";

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

/** Typed wrappers around the backend auth endpoints. */
export const authApi = {
  register: async (payload: RegisterPayload): Promise<User> => {
    const { data } = await apiClient.post<User>("/auth/register", payload);
    return data;
  },

  login: async (payload: LoginPayload): Promise<TokenPair> => {
    const { data } = await apiClient.post<TokenPair>("/auth/login", payload);
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },
};
