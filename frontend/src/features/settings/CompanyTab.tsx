import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { companyApi, type CompanyUpdatePayload } from "@/lib/api/company";
import { getApiErrorMessage } from "@/lib/api/client";

export function CompanyTab() {
  const { company, user, refresh } = useAuth();
  const canEdit = user?.role === "admin" || user?.is_superuser;

  const [form, setForm] = useState({
    name: company?.name ?? "",
    industry: company?.industry ?? "",
    currency: company?.currency ?? "USD",
    timezone: company?.timezone ?? "UTC",
    phone: company?.phone ?? "",
    address: company?.address ?? "",
  });
  const [saving, setSaving] = useState(false);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const onSave = async () => {
    setSaving(true);
    try {
      const payload: CompanyUpdatePayload = {
        name: form.name.trim(),
        industry: form.industry.trim() || null,
        currency: form.currency.trim().toUpperCase(),
        timezone: form.timezone.trim(),
        phone: form.phone.trim() || null,
        address: form.address.trim() || null,
      };
      await companyApi.update(payload);
      await refresh();
      toast.success("Company settings saved.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Company</CardTitle>
        <CardDescription>
          {canEdit
            ? "Your business profile and accounting defaults."
            : "Only admins can edit company settings."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Company name</Label>
          <Input id="name" value={form.name} onChange={set("name")} disabled={!canEdit} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="industry">Industry</Label>
            <Input
              id="industry"
              placeholder="e.g. Retail"
              value={form.industry}
              onChange={set("industry")}
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">Currency</Label>
            <Input
              id="currency"
              maxLength={3}
              value={form.currency}
              onChange={set("currency")}
              disabled={!canEdit}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Input id="timezone" value={form.timezone} onChange={set("timezone")} disabled={!canEdit} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" value={form.phone} onChange={set("phone")} disabled={!canEdit} />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="address">Address</Label>
          <Input id="address" value={form.address} onChange={set("address")} disabled={!canEdit} />
        </div>
        {canEdit && (
          <div className="flex justify-end">
            <Button onClick={onSave} loading={saving}>
              Save changes
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
