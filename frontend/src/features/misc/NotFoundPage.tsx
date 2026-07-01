import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-bold text-primary">404</p>
      <p className="text-lg text-muted-foreground">This page could not be found.</p>
      <Button asChild>
        <Link to="/">Back to dashboard</Link>
      </Button>
    </div>
  );
}
