import { useQuery } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { NewSaleDialog } from "@/features/sales/NewSaleDialog";
import { useAuth } from "@/hooks/useAuth";
import { salesApi } from "@/lib/api/sales";
import { formatMoney } from "@/lib/money";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function SalesPage() {
  const { company } = useAuth();
  const currency = company?.currency ?? "USD";
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: sales, isLoading } = useQuery({ queryKey: ["sales"], queryFn: salesApi.list });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Sales"
        subtitle="Record sales and invoices. Completed sales update stock automatically."
        action={
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4" /> New sale
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : sales && sales.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reference</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sales.map((sale) => (
                  <TableRow key={sale.id}>
                    <TableCell className="font-mono text-xs">{sale.reference}</TableCell>
                    <TableCell>{sale.customer?.name ?? "Walk-in"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {sale.items.reduce((n, i) => n + i.quantity, 0)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(sale.created_at)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatMoney(sale.total, currency)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-10 text-center text-sm text-muted-foreground">
              No sales yet. Record your first sale.
            </p>
          )}
        </CardContent>
      </Card>

      <NewSaleDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
