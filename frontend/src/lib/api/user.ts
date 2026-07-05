import { apiClient } from "@/lib/api/client";
import type { User } from "@/types/auth";

export const userApi = {
  updateProfile: async (fullName: string): Promise<User> => {
    const { data } = await apiClient.patch<User>("/users/me", { full_name: fullName });
    return data;
  },
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post("/users/me/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
