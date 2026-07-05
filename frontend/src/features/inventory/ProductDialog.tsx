import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getApiErrorMessage } from "@/lib/api/client";
import { productsApi, type ProductInput } from "@/lib/api/products";
import { toCents, toMajor } from "@/lib/money";
import type { Product, Supplier } from "@/types/inventory";

const NONE = "none";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product | null;
  suppliers: Supplier[];
}

export function ProductDialog({ open, onOpenChange, product, suppliers }: Props) {
  const queryClient = useQueryClient();
  const isEdit = product !== null;

  const [form, setForm] = useState({
    name: "",
    sku: "",
    category: "",
    unit_price: "",
    cost_price: "",
    quantity: "0",
    reorder_level: "0",
    supplier_id: NONE,
  });

  // Re-seed the form whenever the dialog opens for a (new) product.
  useEffect(() => {
    if (!open) return;
    setForm({
      name: product?.name ?? "",
      sku: product?.sku ?? "",
      category: product?.category ?? "",
      unit_price: product ? String(toMajor(product.unit_price)) : "",
      cost_price: product ? String(toMajor(product.cost_price)) : "",
      quantity: product ? String(product.quantity) : "0",
      reorder_level: String(product?.reorder_level ?? 0),
      supplier_id: product?.supplier_id ? String(product.supplier_id) : NONE,
    });
  }, [open, product]);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const mutation = useMutation({
    mutationFn: (payload: ProductInput) =>
      isEdit ? productsApi.update(product.id, payload) : productsApi.create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success(isEdit ? "Product updated." : "Product created.");
      onOpenChange(false);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  const onSubmit = () => {
    if (!form.name.trim() || !form.sku.trim()) {
      toast.error("Name and SKU are required.");
      return;
    }
    const payload: ProductInput = {
      name: form.name.trim(),
      sku: form.sku.trim(),
      category: form.category.trim() || null,
      unit_price: toCents(form.unit_price || "0"),
      cost_price: toCents(form.cost_price || "0"),
      reorder_level: Number.parseInt(form.reorder_level || "0", 10),
      supplier_id: form.supplier_id === NONE ? null : Number.parseInt(form.supplier_id, 10),
    };
    if (!isEdit) payload.quantity = Number.parseInt(form.quantity || "0", 10);
    mutation.mutate(payload);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit product" : "New product"}</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="p_name">Name</Label>
            <Input id="p_name" value={form.name} onChange={set("name")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="p_sku">SKU</Label>
            <Input id="p_sku" value={form.sku} onChange={set("sku")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="p_cat">Category</Label>
            <Input id="p_cat" value={form.category} onChange={set("category")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="p_price">Selling price</Label>
            <Input id="p_price" type="number" min="0" step="0.01" value={form.unit_price} onChange={set("unit_price")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="p_cost">Cost price</Label>
            <Input id="p_cost" type="number" min="0" step="0.01" value={form.cost_price} onChange={set("cost_price")} />
          </div>
          {!isEdit && (
            <div className="space-y-2">
              <Label htmlFor="p_qty">Initial quantity</Label>
              <Input id="p_qty" type="number" min="0" value={form.quantity} onChange={set("quantity")} />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="p_reorder">Reorder level</Label>
            <Input id="p_reorder" type="number" min="0" value={form.reorder_level} onChange={set("reorder_level")} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Supplier</Label>
            <Select
              value={form.supplier_id}
              onValueChange={(v) => setForm((prev) => ({ ...prev, supplier_id: v }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="No supplier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>No supplier</SelectItem>
                {suppliers.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} loading={mutation.isPending}>
            {isEdit ? "Save changes" : "Create product"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
