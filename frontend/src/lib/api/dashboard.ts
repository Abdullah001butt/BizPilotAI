import { apiClient } from "@/lib/api/client";
import type { DashboardResponse } from "@/types/dashboard";

export const dashboardApi = {
  get: async (): Promise<DashboardResponse> =>
    (await apiClient.get<DashboardResponse>("/dashboard")).data,
};
