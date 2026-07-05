import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Loader2, Sparkles } from "lucide-react";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { billingApi } from "@/lib/api/billing";
import { getApiErrorMessage } from "@/lib/api/client";

const PRO_FEATURES = [
  "AI Copilot — ask anything about your business",
  "Unlimited products, sales, and customers",
  "Priority support",
];

export function BillingTab() {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();

  const { data: config } = useQuery({ queryKey: ["billing-config"], queryFn: billingApi.config });
  const { data: sub, isLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: billingApi.subscription,
  });

  // Handle the redirect back from Stripe Checkout.
  useEffect(() => {
    const result = params.get("billing");
    if (!result) return;
    if (result === "success") {
      toast.success("Welcome to Pro! Your subscription is active.");
      void queryClient.invalidateQueries({ queryKey: ["subscription"] });
    } else if (result === "cancelled") {
      toast.info("Checkout cancelled.");
    }
    params.delete("billing");
    setParams(params, { replace: true });
  }, [params, setParams, queryClient]);

  const checkout = useMutation({
    mutationFn: billingApi.checkout,
    onSuccess: (url) => {
      window.location.href = url;
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const portal = useMutation({
    mutationFn: billingApi.portal,
    onSuccess: (url) => {
      window.location.href = url;
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isPro = sub?.is_pro ?? false;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Plan &amp; billing</CardTitle>
        <CardDescription>
          {isPro
            ? "You're on the Pro plan."
            : "You're on the Free plan. Upgrade to unlock the AI Copilot."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Current plan badge */}
        <div className="flex items-center justify-between rounded-lg border border-border p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <p className="font-medium capitalize">{sub?.plan ?? "free"} plan</p>
              <p className="text-xs capitalize text-muted-foreground">{sub?.status ?? "free"}</p>
            </div>
          </div>
          {isPro && (
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-500">
              Active
            </span>
          )}
        </div>

        {/* Pro benefits */}
        <ul className="space-y-2">
          {PRO_FEATURES.map((f) => (
            <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="h-4 w-4 shrink-0 text-emerald-500" />
              {f}
            </li>
          ))}
        </ul>

        {/* Actions */}
        {!config?.configured ? (
          <p className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
            Billing isn&apos;t enabled on this deployment. Add Stripe keys to the backend to
            enable subscriptions.
          </p>
        ) : isPro ? (
          <Button variant="outline" onClick={() => portal.mutate()} loading={portal.isPending}>
            Manage billing
          </Button>
        ) : (
          <Button onClick={() => checkout.mutate()} loading={checkout.isPending}>
            <Sparkles className="h-4 w-4" /> Upgrade to Pro
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
