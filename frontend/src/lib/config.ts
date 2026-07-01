/** Centralised, typed access to build-time environment configuration. */
export const config = {
  /** Backend API base URL. Defaults to the dev proxy path. */
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  /** localStorage key under which the refresh token is persisted. */
  refreshTokenKey: "bizpilot.refresh_token",
} as const;
