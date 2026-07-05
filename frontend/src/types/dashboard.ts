export interface DashboardKpis {
  revenue_total: number;
  revenue_this_month: number;
  profit_this_month: number;
  sales_count: number;
  sales_today_count: number;
  sales_today_amount: number;
}

export interface InventorySummary {
  product_count: number;
  low_stock_count: number;
  stock_value: number;
}

export interface TrendPoint {
  month: string;
  revenue: number;
  profit: number;
}

export interface TopProduct {
  product_id: number;
  name: string;
  units_sold: number;
  revenue: number;
}

export interface RecentSale {
  id: number;
  reference: string;
  customer_name: string | null;
  total: number;
  created_at: string;
}

export interface DashboardResponse {
  kpis: DashboardKpis;
  inventory: InventorySummary;
  customers_count: number;
  health_score: number;
  health_label: string;
  revenue_trend: TrendPoint[];
  top_products: TopProduct[];
  recent_sales: RecentSale[];
}
