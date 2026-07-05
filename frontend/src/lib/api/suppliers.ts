import { apiClient } from "@/lib/api/client";
import type { Supplier } from "@/types/inventory";

export interface SupplierInput {
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  notes?: string | null;
}

export const suppliersApi = {
  list: async (): Promise<Supplier[]> => (await apiClient.get<Supplier[]>("/suppliers")).data,
  create: async (input: SupplierInput): Promise<Supplier> =>
    (await apiClient.post<Supplier>("/suppliers", input)).data,
  update: async (id: number, input: Partial<SupplierInput>): Promise<Supplier> =>
    (await apiClient.patch<Supplier>(`/suppliers/${id}`, input)).data,
  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/suppliers/${id}`);
  },
};
