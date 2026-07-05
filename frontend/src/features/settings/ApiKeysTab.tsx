import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, KeyRound, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { apiKeysApi } from "@/lib/api/apiKeys";
import { getApiErrorMessage } from "@/lib/api/client";

export function ApiKeysTab() {
  const { user } = useAuth();
  const canManage = user?.role === "admin" || user?.is_superuser;
  const queryClient = useQueryClient();

  const [newName, setNewName] = useState("");
  const [freshKey, setFreshKey] = useState<string | null>(null);

  const { data: keys, isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: apiKeysApi.list,
    enabled: canManage,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(name),
    onSuccess: (created) => {
      setFreshKey(created.key);
      setNewName("");
      void queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key created.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  const revokeMutation = useMutation({
    mutationFn: (id: number) => apiKeysApi.revoke(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key revoked.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  const copyKey = async () => {
    if (!freshKey) return;
    await navigator.clipboard.writeText(freshKey);
    toast.success("Copied to clipboard.");
  };

  if (!canManage) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Only company admins can manage API keys.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">API Keys</CardTitle>
        <CardDescription>
          Create keys for programmatic access. Store them securely — they&apos;re shown only once.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* One-time reveal of a freshly created key */}
        {freshKey && (
          <div className="space-y-2 rounded-lg border border-primary/40 bg-primary/5 p-4">
            <p className="text-sm font-medium">Your new API key</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded bg-background px-3 py-2 font-mono text-sm">
                {freshKey}
              </code>
              <Button variant="outline" size="icon" onClick={copyKey} aria-label="Copy key">
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Copy it now — you won&apos;t be able to see it again.
            </p>
            <Button variant="ghost" size="sm" onClick={() => setFreshKey(null)}>
              Done
            </Button>
          </div>
        )}

        {/* Create form */}
        <div className="flex items-end gap-2">
          <div className="flex-1 space-y-2">
            <label htmlFor="key_name" className="text-sm font-medium">
              New key name
            </label>
            <Input
              id="key_name"
              placeholder="e.g. Production server"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>
          <Button
            onClick={() => createMutation.mutate(newName.trim())}
            disabled={newName.trim().length === 0}
            loading={createMutation.isPending}
          >
            Create key
          </Button>
        </div>

        <Separator />

        {/* Existing keys */}
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : keys && keys.length > 0 ? (
          <ul className="divide-y divide-border">
            {keys.map((key) => (
              <li key={key.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                    <KeyRound className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm font-medium">
                      {key.name}
                      {key.revoked && (
                        <span className="ml-2 rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium uppercase text-destructive">
                          Revoked
                        </span>
                      )}
                    </p>
                    <p className="font-mono text-xs text-muted-foreground">{key.prefix}…</p>
                  </div>
                </div>
                {!key.revoked && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => revokeMutation.mutate(key.id)}
                    aria-label="Revoke key"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-4 text-center text-sm text-muted-foreground">No API keys yet.</p>
        )}
      </CardContent>
    </Card>
  );
}
