import { motion } from "framer-motion";
import {
  Activity,
  ArrowUpRight,
  DollarSign,
  Package,
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

// NOTE: Phase 1 ships the dashboard *shell* with representative sample data.
// Live metrics are wired to real modules (sales, inventory, expenses) in later
// phases — the layout and data contracts are intentionally established now.
const REVENUE_TREND = [
  { month: "Jan", revenue: 42000, expenses: 28000 },
  { month: "Feb", revenue: 47800, expenses: 30100 },
  { month: "Mar", revenue: 51200, expenses: 29800 },
  { month: "Apr", revenue: 49600, expenses: 31500 },
  { month: "May", revenue: 58900, expenses: 33200 },
  { month: "Jun", revenue: 64300, expenses: 34800 },
];

const STATS = [
  { label: "Monthly Revenue", value: "$64,300", delta: "+9.2%", icon: DollarSign },
  { label: "Net Profit", value: "$29,500", delta: "+12.4%", icon: TrendingUp },
  { label: "Active Products", value: "182", delta: "+4", icon: Package },
  { label: "Business Health", value: "87 / 100", delta: "Healthy", icon: Activity },
];

const currency = (value: number) => `$${(value / 1000).toFixed(0)}k`;

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          A snapshot of your business. Signed in as{" "}
          <span className="font-medium capitalize text-foreground">{user?.role}</span>.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((stat, index) => {
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
                    <span className="inline-flex items-center gap-0.5 text-xs font-medium text-emerald-500">
                      <ArrowUpRight className="h-3 w-3" />
                      {stat.delta}
                    </span>
                  </div>
                  <p className="mt-4 text-2xl font-semibold">{stat.value}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Revenue vs expenses */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Revenue vs. Expenses</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={REVENUE_TREND} margin={{ left: -16, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(243 75% 59%)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="hsl(243 75% 59%)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(0 72% 51%)" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="hsl(0 72% 51%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickFormatter={currency}
                />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                    fontSize: "0.8rem",
                  }}
                  formatter={(value: number) => `$${value.toLocaleString()}`}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="hsl(243 75% 59%)"
                  strokeWidth={2}
                  fill="url(#revFill)"
                  name="Revenue"
                />
                <Area
                  type="monotone"
                  dataKey="expenses"
                  stroke="hsl(0 72% 51%)"
                  strokeWidth={2}
                  fill="url(#expFill)"
                  name="Expenses"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="border-dashed">
        <CardContent className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
          <Sparkle />
          You&apos;re on <span className="font-medium text-foreground">Phase 1</span> — authentication
          and the application shell. Inventory, Sales, CRM, and the AI Copilot arrive in upcoming
          phases.
        </CardContent>
      </Card>
    </div>
  );
}

function Sparkle() {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
      <TrendingUp className="h-4 w-4" />
    </span>
  );
}
