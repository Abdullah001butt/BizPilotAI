import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Outlet } from "react-router-dom";

/** Split-screen branded shell wrapping the login/register forms. */
export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand / marketing panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-primary via-indigo-600 to-violet-700 p-12 text-white lg:flex">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <Sparkles className="h-6 w-6" />
          BizPilot AI
        </div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="max-w-md space-y-4"
        >
          <h1 className="text-4xl font-bold leading-tight">
            Run your business smarter with AI.
          </h1>
          <p className="text-lg text-white/80">
            Intelligence, inventory, CRM, accounting, and forecasting — unified in
            one premium operating system for modern SMBs.
          </p>
        </motion.div>
        <p className="text-sm text-white/60">
          © {new Date().getFullYear()} BizPilot AI. All rights reserved.
        </p>
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-violet-400/20 blur-3xl" />
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
