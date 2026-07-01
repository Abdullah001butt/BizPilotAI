import { config } from "@/lib/config";

/**
 * Token storage strategy:
 *  - Access token lives in memory only (cleared on refresh/tab close) — never in
 *    localStorage, which limits XSS blast radius.
 *  - Refresh token is persisted to localStorage so sessions survive reloads.
 */
let accessToken: string | null = null;

export const tokenStore = {
  getAccessToken: (): string | null => accessToken,
  setAccessToken: (token: string | null): void => {
    accessToken = token;
  },

  getRefreshToken: (): string | null =>
    localStorage.getItem(config.refreshTokenKey),
  setRefreshToken: (token: string | null): void => {
    if (token) localStorage.setItem(config.refreshTokenKey, token);
    else localStorage.removeItem(config.refreshTokenKey);
  },

  clear: (): void => {
    accessToken = null;
    localStorage.removeItem(config.refreshTokenKey);
  },
};
