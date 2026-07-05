import { useCallback, useEffect, useMemo, useState } from "react";

import { AUTH_LOGOUT_EVENT } from "@/lib/api/client";
import { authApi, type LoginPayload, type RegisterPayload } from "@/lib/api/auth";
import { tokenStore } from "@/lib/api/tokenStore";
import { AuthContext, type AuthContextValue, type AuthStatus } from "@/context/auth-context";
import type { Company, User } from "@/types/auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  // Bootstrap: if a refresh token is persisted, restore the session by fetching
  // the profile (the API client transparently refreshes the access token).
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!tokenStore.getRefreshToken()) {
        setStatus("unauthenticated");
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) {
          setUser(me.user);
          setCompany(me.company);
          setStatus("authenticated");
        }
      } catch {
        if (!cancelled) {
          tokenStore.clear();
          setStatus("unauthenticated");
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  // React to an unrecoverable session (refresh failed mid-session).
  useEffect(() => {
    const handleForcedLogout = () => {
      setUser(null);
      setCompany(null);
      setStatus("unauthenticated");
    };
    window.addEventListener(AUTH_LOGOUT_EVENT, handleForcedLogout);
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, handleForcedLogout);
  }, []);

  const hydrateSession = useCallback(async () => {
    const me = await authApi.me();
    setUser(me.user);
    setCompany(me.company);
    setStatus("authenticated");
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const tokens = await authApi.login(payload);
      tokenStore.setAccessToken(tokens.access_token);
      tokenStore.setRefreshToken(tokens.refresh_token);
      await hydrateSession();
    },
    [hydrateSession],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await authApi.register(payload);
      await login({ email: payload.email, password: payload.password });
    },
    [login],
  );

  const logout = useCallback(async () => {
    const refreshToken = tokenStore.getRefreshToken();
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } finally {
      tokenStore.clear();
      setUser(null);
      setCompany(null);
      setStatus("unauthenticated");
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, company, status, login, register, logout, refresh: hydrateSession }),
    [user, company, status, login, register, logout, hydrateSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
