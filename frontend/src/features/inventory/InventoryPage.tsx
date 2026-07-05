import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Minus, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ContactFormDialog, type ContactValues } from "@/features/inventory/ContactFormDialog";
import { ProductDialog } from "@/features/inventory/ProductDialog";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/lib/api/client";
import { productsApi } from "@/lib/api/products";
import { suppliersApi } from "@/lib/api/suppliers";
import { formatMoney } from "@/lib/money";
import type { Product, Supplier } from "@/types/inventory";

function Loading() {
  return (
    <div className="flex justify-center py-10">
      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
    </div>
  );
}

function ProductsTab() {
  const { company } = useAuth();
  const currency = company?.currency ?? "USD";
  const queryClient = useQueryClient();

  const { data: products, isLoading } = useQuery({ queryKey: ["products"], queryFn: productsApi.list });
  const { data: suppliers } = useQuery({ queryKey: ["suppliers"], queryFn: suppliersApi.list });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["products"] });

  const adjust = useMutation({
    mutationFn: ({ id, change }: { id: number; change: number }) =>
      productsApi.adjustStock(id, change),
    onSuccess: () => void invalidate(),
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => productsApi.remove(id),
    onSuccess: () => {
      void invalidate();
      toast.success("Product deleted.");
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const openNew = () => {
    setEditing(null);
    setDialogOpen(true);
  };
  const openEdit = (p: Product) => {
    setEditing(p);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={openNew}>
          <Plus className="h-4 w-4" /> New product
        </Button>
      </div>
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <Loading />
          ) : products && products.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Stock</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">{p.sku}</TableCell>
                    <TableCell>{formatMoney(p.unit_price, currency)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => adjust.mutate({ id: p.id, change: -1 })}
                          aria-label="Decrease stock"
                        >
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span
                          className={
                            p.is_low_stock ? "font-semibold text-destructive" : "font-medium"
                          }
                        >
                          {p.quantity}
                        </span>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => adjust.mutate({ id: p.id, change: 1 })}
                          aria-label="Increase stock"
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                        {p.is_low_stock && (
                          <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium uppercase text-destructive">
                            Low
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(p)} aria-label="Edit">
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => remove.mutate(p.id)}
                        aria-label="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-10 text-center text-sm text-muted-foreground">
              No products yet. Create your first one.
            </p>
          )}
        </CardContent>
      </Card>

      <ProductDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        product={editing}
        suppliers={suppliers ?? []}
      />
    </div>
  );
}

function SuppliersTab() {
  const queryClient = useQueryClient();
  const { data: suppliers, isLoading } = useQuery({
    queryKey: ["suppliers"],
    queryFn: suppliersApi.list,
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ContactValues | null>(null);

  const remove = useMutation({
    mutationFn: (id: number) => suppliersApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      toast.success("Supplier deleted.");
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const openEdit = (s: Supplier) => {
    setEditing({
      id: s.id,
      name: s.name,
      email: s.email ?? "",
      phone: s.phone ?? "",
      address: s.address ?? "",
      notes: s.notes ?? "",
    });
    setDialogOpen(true);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> New supplier
        </Button>
      </div>
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <Loading />
          ) : suppliers && suppliers.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">{s.name}</TableCell>
                    <TableCell className="text-muted-foreground">{s.email ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{s.phone ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(s)} aria-label="Edit">
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => remove.mutate(s.id)}
                        aria-label="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-10 text-center text-sm text-muted-foreground">No suppliers yet.</p>
          )}
        </CardContent>
      </Card>

      <ContactFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        entityLabel="Supplier"
        queryKey="suppliers"
        initial={editing}
        create={suppliersApi.create}
        update={suppliersApi.update}
      />
    </div>
  );
}

export function InventoryPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader title="Inventory" subtitle="Manage products, stock, and suppliers." />
      <Tabs defaultValue="products">
        <TabsList>
          <TabsTrigger value="products">Products</TabsTrigger>
          <TabsTrigger value="suppliers">Suppliers</TabsTrigger>
        </TabsList>
        <TabsContent value="products">
          <ProductsTab />
        </TabsContent>
        <TabsContent value="suppliers">
          <SuppliersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
