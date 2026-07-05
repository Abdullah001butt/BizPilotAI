import { apiClient } from "@/lib/api/client";
import type { Customer } from "@/types/inventory";

export interface CustomerInput {
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  notes?: string | null;
}

export const customersApi = {
  list: async (): Promise<Customer[]> => (await apiClient.get<Customer[]>("/customers")).data,
  create: async (input: CustomerInput): Promise<Customer> =>
    (await apiClient.post<Customer>("/customers", input)).data,
  update: async (id: number, input: Partial<CustomerInput>): Promise<Customer> =>
    (await apiClient.patch<Customer>(`/customers/${id}`, input)).data,
  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/customers/${id}`);
  },
};
