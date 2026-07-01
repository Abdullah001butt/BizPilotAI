import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import { config } from "@/lib/config";
import { tokenStore } from "@/lib/api/tokenStore";
import type { ApiErrorBody, TokenPair } from "@/types/auth";

/** Emitted when the session can no longer be recovered (refresh failed). */
export const AUTH_LOGOUT_EVENT = "bizpilot:auth-logout";

export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  headers: { "Content-Type": "application/json" },
});

// Attach the access token to every outgoing request.
apiClient.interceptors.request.use((req: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccessToken();
  if (token) req.headers.Authorization = `Bearer ${token}`;
  return req;
});

// ── Transparent token refresh on 401 ──────────────────────────────────────────
// A single in-flight refresh is shared by all concurrent 401s (no stampede).
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStore.getRefreshToken();
  if (!refreshToken) throw new Error("No refresh token available.");

  // Use a bare axios call so this request never re-enters the interceptor chain.
  const { data } = await axios.post<TokenPair>(
    `${config.apiBaseUrl}/auth/refresh`,
    { refresh_token: refreshToken },
    { headers: { "Content-Type": "application/json" } },
  );
  tokenStore.setAccessToken(data.access_token);
  tokenStore.setRefreshToken(data.refresh_token);
  return data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as
      | (AxiosRequestConfig & { _retried?: boolean })
      | undefined;

    // A 401 from login/register/logout is a real credential failure, not an
    // expired access token — don't attempt a refresh for those. `/auth/me` and
    // all other endpoints SHOULD trigger a refresh-and-retry.
    const url = original?.url ?? "";
    const isAuthEndpoint =
      url.includes("/auth/login") ||
      url.includes("/auth/register") ||
      url.includes("/auth/logout");
    const shouldTryRefresh =
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !isAuthEndpoint &&
      tokenStore.getRefreshToken();

    if (shouldTryRefresh) {
      original._retried = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const newToken = await refreshPromise;
        original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` };
        return apiClient(original);
      } catch {
        tokenStore.clear();
        window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
      }
    }
    return Promise.reject(error);
  },
);

/** Extract a human-readable message from an API error response. */
export function getApiErrorMessage(error: unknown, fallback = "Something went wrong."): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined;
    return body?.error?.message ?? error.message ?? fallback;
  }
  return fallback;
}
