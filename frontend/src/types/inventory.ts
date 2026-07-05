export interface Supplier {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  description: string | null;
  category: string | null;
  barcode: string | null;
  /** Selling price in minor units (cents). */
  unit_price: number;
  /** Cost price in minor units (cents). */
  cost_price: number;
  quantity: number;
  reorder_level: number;
  supplier_id: number | null;
  is_active: boolean;
  is_low_stock: boolean;
  created_at: string;
}

export interface Customer {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  created_at: string;
}

export type SaleStatus = "draft" | "completed" | "cancelled";

export interface SaleItem {
  id: number;
  product_id: number | null;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface Sale {
  id: number;
  reference: string;
  customer_id: number | null;
  customer: { id: number; name: string } | null;
  status: SaleStatus;
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  notes: string | null;
  created_at: string;
  items: SaleItem[];
}
