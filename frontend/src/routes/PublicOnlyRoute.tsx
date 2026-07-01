import { Loader2 } from "lucide-react";
import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

/** Keeps already-authenticated users out of login/register, sending them home. */
export function PublicOnlyRoute() {
  const { status } = useAuth();

  if (status === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
