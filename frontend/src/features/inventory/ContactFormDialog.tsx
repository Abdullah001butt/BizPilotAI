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
import { getApiErrorMessage } from "@/lib/api/client";

export interface ContactValues {
  id?: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
}

export interface ContactPayload {
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entityLabel: string;
  queryKey: string;
  initial: ContactValues | null;
  create: (payload: ContactPayload) => Promise<unknown>;
  update: (id: number, payload: ContactPayload) => Promise<unknown>;
}

/** Reused for both suppliers and customers — they share the same contact shape. */
export function ContactFormDialog({
  open,
  onOpenChange,
  entityLabel,
  queryKey,
  initial,
  create,
  update,
}: Props) {
  const queryClient = useQueryClient();
  const isEdit = initial?.id !== undefined;

  const [form, setForm] = useState<ContactValues>({
    name: "",
    email: "",
    phone: "",
    address: "",
    notes: "",
  });

  useEffect(() => {
    if (!open) return;
    setForm({
      name: initial?.name ?? "",
      email: initial?.email ?? "",
      phone: initial?.phone ?? "",
      address: initial?.address ?? "",
      notes: initial?.notes ?? "",
    });
  }, [open, initial]);

  const set = (key: keyof ContactValues) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const mutation = useMutation({
    mutationFn: (payload: ContactPayload) =>
      initial?.id !== undefined ? update(initial.id, payload) : create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [queryKey] });
      toast.success(`${entityLabel} saved.`);
      onOpenChange(false);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  const onSubmit = () => {
    if (!form.name.trim()) {
      toast.error("Name is required.");
      return;
    }
    mutation.mutate({
      name: form.name.trim(),
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      address: form.address.trim() || null,
      notes: form.notes.trim() || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? `Edit ${entityLabel.toLowerCase()}` : `New ${entityLabel.toLowerCase()}`}
          </DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="c_name">Name</Label>
            <Input id="c_name" value={form.name} onChange={set("name")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="c_email">Email</Label>
            <Input id="c_email" type="email" value={form.email} onChange={set("email")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="c_phone">Phone</Label>
            <Input id="c_phone" value={form.phone} onChange={set("phone")} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="c_addr">Address</Label>
            <Input id="c_addr" value={form.address} onChange={set("address")} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="c_notes">Notes</Label>
            <Input id="c_notes" value={form.notes} onChange={set("notes")} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} loading={mutation.isPending}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
