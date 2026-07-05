import { apiClient } from "@/lib/api/client";
import type { Product } from "@/types/inventory";

export interface ProductInput {
  name: string;
  sku: string;
  description?: string | null;
  category?: string | null;
  barcode?: string | null;
  unit_price: number; // cents
  cost_price?: number; // cents
  quantity?: number;
  reorder_level?: number;
  supplier_id?: number | null;
  is_active?: boolean;
}

export const productsApi = {
  list: async (): Promise<Product[]> => (await apiClient.get<Product[]>("/products")).data,
  lowStock: async (): Promise<Product[]> =>
    (await apiClient.get<Product[]>("/products/low-stock")).data,
  create: async (input: ProductInput): Promise<Product> =>
    (await apiClient.post<Product>("/products", input)).data,
  update: async (id: number, input: Partial<ProductInput>): Promise<Product> =>
    (await apiClient.patch<Product>(`/products/${id}`, input)).data,
  adjustStock: async (id: number, change: number, reason = "adjustment"): Promise<Product> =>
    (await apiClient.post<Product>(`/products/${id}/stock`, { change, reason })).data,
  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/products/${id}`);
  },
};
