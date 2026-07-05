import { apiClient } from "@/lib/api/client";
import type { Sale } from "@/types/inventory";

export interface SaleItemInput {
  product_id: number;
  quantity: number;
  unit_price?: number; // cents; defaults to product price
}

export interface SaleInput {
  customer_id?: number | null;
  items: SaleItemInput[];
  discount?: number; // cents
  tax?: number; // cents
  reference?: string;
  notes?: string;
}

export const salesApi = {
  list: async (): Promise<Sale[]> => (await apiClient.get<Sale[]>("/sales")).data,
  get: async (id: number): Promise<Sale> => (await apiClient.get<Sale>(`/sales/${id}`)).data,
  create: async (input: SaleInput): Promise<Sale> =>
    (await apiClient.post<Sale>("/sales", input)).data,
};
