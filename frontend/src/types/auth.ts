export type UserRole = "admin" | "manager" | "employee";

export interface User {
  id: number;
  company_id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  slug: string;
  industry: string | null;
  currency: string;
  timezone: string;
  fiscal_year_start_month: number;
  phone: string | null;
  address: string | null;
  logo_url: string | null;
  preferences: Record<string, unknown>;
  created_at: string;
}

/** Response of GET /auth/me — the user together with their company. */
export interface MeResponse {
  user: User;
  company: Company;
}

export interface ApiKey {
  id: number;
  name: string;
  prefix: string;
  last_used_at: string | null;
  revoked: boolean;
  created_at: string;
}

/** Returned once, on creation — includes the plaintext secret. */
export interface ApiKeyCreated extends ApiKey {
  key: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Shape of the uniform error envelope returned by the backend. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
