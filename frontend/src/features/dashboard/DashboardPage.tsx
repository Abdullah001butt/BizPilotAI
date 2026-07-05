import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  DollarSign,
  Loader2,
  ShoppingCart,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api/dashboard";
import { formatMoney } from "@/lib/money";
import type { DashboardResponse } from "@/types/dashboard";

function healthColor(score: number): string {
  if (score >= 80) return "text-emerald-500";
  if (score >= 60) return "text-primary";
  if (score >= 40) return "text-amber-500";
  return "text-destructive";
}

export function DashboardPage() {
  const { user, company } = useAuth();
  const currency = company?.currency ?? "USD";

  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboardApi.get,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (isError || !data) {
    return <p className="text-sm text-destructive">Failed to load dashboard.</p>;
  }

  const money = (cents: number) => formatMoney(cents, currency);
  const stats = buildStats(data, money);
  const trendData = data.revenue_trend.map((p) => ({
    month: p.month,
    revenue: p.revenue / 100,
    profit: p.profit / 100,
  }));

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Welcome back, {user?.full_name}. Here&apos;s how {company?.name} is doing.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: index * 0.06 }}
            >
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </span>
                    {stat.hint && (
                      <span className="text-xs text-muted-foreground">{stat.hint}</span>
                    )}
                  </div>
                  <p className={`mt-4 text-2xl font-semibold ${stat.valueClass ?? ""}`}>
                    {stat.value}
                  </p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Low-stock alert */}
      {data.inventory.low_stock_count > 0 && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span>
            <span className="font-medium">{data.inventory.low_stock_count}</span> product
            {data.inventory.low_stock_count > 1 ? "s are" : " is"} at or below the reorder level.
          </span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trend chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Revenue vs. Profit (6 months)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ left: -12, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(243 75% 59%)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="hsl(243 75% 59%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="prof" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(160 84% 39%)" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(160 84% 39%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "0.5rem",
                      fontSize: "0.8rem",
                    }}
                    formatter={(value: number) => money(Math.round(value * 100))}
                  />
                  <Area type="monotone" dataKey="revenue" name="Revenue" stroke="hsl(243 75% 59%)" strokeWidth={2} fill="url(#rev)" />
                  <Area type="monotone" dataKey="profit" name="Profit" stroke="hsl(160 84% 39%)" strokeWidth={2} fill="url(#prof)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Health score */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Business Health</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-6">
            <div className={`text-5xl font-bold ${healthColor(data.health_score)}`}>
              {data.health_score}
              <span className="text-xl text-muted-foreground">/100</span>
            </div>
            <span className={`text-sm font-medium ${healthColor(data.health_score)}`}>
              {data.health_label}
            </span>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${data.health_score}%` }}
              />
            </div>
            <p className="text-center text-xs text-muted-foreground">
              Composite of profit margin, stock health, and sales activity.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top products */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Products</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_products.length > 0 ? (
              <ul className="space-y-3">
                {data.top_products.map((p, i) => (
                  <li key={p.product_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-muted text-xs font-medium">
                        {i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium">{p.name}</p>
                        <p className="text-xs text-muted-foreground">{p.units_sold} sold</p>
                      </div>
                    </div>
                    <span className="text-sm font-medium">{money(p.revenue)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">No sales yet.</p>
            )}
          </CardContent>
        </Card>

        {/* Recent sales */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Sales</CardTitle>
          </CardHeader>
          <CardContent>
            {data.recent_sales.length > 0 ? (
              <ul className="space-y-3">
                {data.recent_sales.map((s) => (
                  <li key={s.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-mono text-xs">{s.reference}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.customer_name ?? "Walk-in"}
                      </p>
                    </div>
                    <span className="text-sm font-medium">{money(s.total)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">No sales yet.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

type Stat = {
  label: string;
  value: string;
  icon: typeof DollarSign;
  hint?: string;
  valueClass?: string;
};

function buildStats(data: DashboardResponse, money: (c: number) => string): Stat[] {
  return [
    {
      label: "Revenue (this month)",
      value: money(data.kpis.revenue_this_month),
      icon: DollarSign,
      hint: `${money(data.kpis.revenue_total)} all-time`,
    },
    {
      label: "Profit (this month)",
      value: money(data.kpis.profit_this_month),
      icon: TrendingUp,
      valueClass: data.kpis.profit_this_month < 0 ? "text-destructive" : undefined,
    },
    {
      label: "Sales today",
      value: String(data.kpis.sales_today_count),
      icon: ShoppingCart,
      hint: money(data.kpis.sales_today_amount),
    },
    {
      label: "Business health",
      value: `${data.health_score} / 100`,
      icon: Activity,
      hint: data.health_label,
    },
  ];
}
