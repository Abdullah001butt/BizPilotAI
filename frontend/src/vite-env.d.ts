/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the backend API, e.g. "/api/v1" (proxied) or a full origin. */
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
