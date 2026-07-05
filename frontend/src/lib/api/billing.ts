import { apiClient } from "@/lib/api/client";

export type PlanTier = "free" | "pro";

export interface Subscription {
  plan: PlanTier;
  status: string;
  is_pro: boolean;
  current_period_end: string | null;
}

export interface BillingConfig {
  configured: boolean;
  publishable_key: string | null;
}

export const billingApi = {
  config: async (): Promise<BillingConfig> =>
    (await apiClient.get<BillingConfig>("/billing/config")).data,
  subscription: async (): Promise<Subscription> =>
    (await apiClient.get<Subscription>("/billing/subscription")).data,
  checkout: async (): Promise<string> =>
    (await apiClient.post<{ url: string }>("/billing/checkout")).data.url,
  portal: async (): Promise<string> =>
    (await apiClient.post<{ url: string }>("/billing/portal")).data.url,
  sync: async (): Promise<Subscription> =>
    (await apiClient.post<Subscription>("/billing/sync")).data,
};
