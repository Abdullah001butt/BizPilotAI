import { apiClient } from "@/lib/api/client";
import type { ApiKey, ApiKeyCreated } from "@/types/auth";

export const apiKeysApi = {
  list: async (): Promise<ApiKey[]> => {
    const { data } = await apiClient.get<ApiKey[]>("/api-keys");
    return data;
  },
  create: async (name: string): Promise<ApiKeyCreated> => {
    const { data } = await apiClient.post<ApiKeyCreated>("/api-keys", { name });
    return data;
  },
  revoke: async (id: number): Promise<void> => {
    await apiClient.delete(`/api-keys/${id}`);
  },
};
