import { Loader2 } from "lucide-react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

/** Gates child routes behind authentication, preserving the intended destination. */
export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
