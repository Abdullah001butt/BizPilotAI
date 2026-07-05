import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "sonner";

import { App } from "@/App";
import { AuthProvider } from "@/context/AuthProvider";
import { queryClient } from "@/lib/queryClient";

import "@/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Root element #root not found.");

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
        <Toaster richColors position="top-right" />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
