import { apiClient } from "@/lib/api/client";
import type { Company } from "@/types/auth";

export interface CompanyUpdatePayload {
  name?: string;
  industry?: string | null;
  currency?: string;
  timezone?: string;
  fiscal_year_start_month?: number;
  phone?: string | null;
  address?: string | null;
  logo_url?: string | null;
  preferences?: Record<string, unknown>;
}

export const companyApi = {
  get: async (): Promise<Company> => {
    const { data } = await apiClient.get<Company>("/company");
    return data;
  },
  update: async (payload: CompanyUpdatePayload): Promise<Company> => {
    const { data } = await apiClient.patch<Company>("/company", payload);
    return data;
  },
};
