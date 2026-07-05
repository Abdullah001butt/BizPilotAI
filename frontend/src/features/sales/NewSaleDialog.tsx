import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/lib/api/client";
import { customersApi } from "@/lib/api/customers";
import { productsApi } from "@/lib/api/products";
import { salesApi, type SaleInput } from "@/lib/api/sales";
import { formatMoney, toCents } from "@/lib/money";

const NO_CUSTOMER = "none";

interface Line {
  product_id: string;
  quantity: string;
}

export function NewSaleDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { company } = useAuth();
  const currency = company?.currency ?? "USD";
  const queryClient = useQueryClient();

  const { data: products } = useQuery({ queryKey: ["products"], queryFn: productsApi.list });
  const { data: customers } = useQuery({ queryKey: ["customers"], queryFn: customersApi.list });

  const [customerId, setCustomerId] = useState(NO_CUSTOMER);
  const [lines, setLines] = useState<Line[]>([{ product_id: "", quantity: "1" }]);
  const [discount, setDiscount] = useState("0");
  const [tax, setTax] = useState("0");

  const productById = useMemo(
    () => new Map((products ?? []).map((p) => [p.id, p])),
    [products],
  );

  const subtotal = useMemo(
    () =>
      lines.reduce((sum, line) => {
        const product = productById.get(Number(line.product_id));
        const qty = Number.parseInt(line.quantity || "0", 10);
        return sum + (product ? product.unit_price * qty : 0);
      }, 0),
    [lines, productById],
  );
  const total = subtotal - toCents(discount || "0") + toCents(tax || "0");

  const reset = () => {
    setCustomerId(NO_CUSTOMER);
    setLines([{ product_id: "", quantity: "1" }]);
    setDiscount("0");
    setTax("0");
  };

  const mutation = useMutation({
    mutationFn: (input: SaleInput) => salesApi.create(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["sales"] });
      void queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Sale recorded.");
      reset();
      onOpenChange(false);
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const updateLine = (index: number, patch: Partial<Line>) =>
    setLines((prev) => prev.map((l, i) => (i === index ? { ...l, ...patch } : l)));

  const onSubmit = () => {
    const items = lines
      .filter((l) => l.product_id && Number.parseInt(l.quantity, 10) > 0)
      .map((l) => ({ product_id: Number(l.product_id), quantity: Number(l.quantity) }));
    if (items.length === 0) {
      toast.error("Add at least one product.");
      return;
    }
    mutation.mutate({
      customer_id: customerId === NO_CUSTOMER ? null : Number(customerId),
      items,
      discount: toCents(discount || "0"),
      tax: toCents(tax || "0"),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New sale</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Customer (optional)</Label>
            <Select value={customerId} onValueChange={setCustomerId}>
              <SelectTrigger>
                <SelectValue placeholder="Walk-in customer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NO_CUSTOMER}>Walk-in customer</SelectItem>
                {(customers ?? []).map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Items</Label>
            {lines.map((line, index) => {
              const product = productById.get(Number(line.product_id));
              return (
                <div key={index} className="flex items-center gap-2">
                  <div className="flex-1">
                    <Select
                      value={line.product_id}
                      onValueChange={(v) => updateLine(index, { product_id: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select product" />
                      </SelectTrigger>
                      <SelectContent>
                        {(products ?? []).map((p) => (
                          <SelectItem key={p.id} value={String(p.id)}>
                            {p.name} · {formatMoney(p.unit_price, currency)} ({p.quantity} in stock)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Input
                    type="number"
                    min="1"
                    className="w-20"
                    value={line.quantity}
                    onChange={(e) => updateLine(index, { quantity: e.target.value })}
                  />
                  <span className="w-24 text-right text-sm text-muted-foreground">
                    {product
                      ? formatMoney(product.unit_price * Number(line.quantity || 0), currency)
                      : "—"}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setLines((prev) => prev.filter((_, i) => i !== index))}
                    disabled={lines.length === 1}
                    aria-label="Remove line"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              );
            })}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLines((prev) => [...prev, { product_id: "", quantity: "1" }])}
            >
              <Plus className="h-4 w-4" /> Add item
            </Button>
          </div>

          <Separator />

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="discount">Discount</Label>
              <Input id="discount" type="number" min="0" step="0.01" value={discount} onChange={(e) => setDiscount(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tax">Tax</Label>
              <Input id="tax" type="number" min="0" step="0.01" value={tax} onChange={(e) => setTax(e.target.value)} />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-muted px-4 py-3">
            <span className="text-sm text-muted-foreground">Total</span>
            <span className="text-lg font-semibold">{formatMoney(Math.max(total, 0), currency)}</span>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} loading={mutation.isPending}>
            Record sale
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
