/** Thin API client. Business rules never live in UI components: the server is authoritative. */

export type ApiStatus = "ok" | "unavailable" | "unreachable";

export async function fetchApiStatus(signal?: AbortSignal): Promise<ApiStatus> {
  try {
    const response = await fetch("/api/v1/health/ready/", { signal });
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "status" in body) {
      return body.status === "ok" ? "ok" : "unavailable";
    }
    return "unavailable";
  } catch {
    return "unreachable";
  }
}

/** Uniform server error envelope: {"error": {"code", "message"}}. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export interface Session {
  token: string;
  tenantId: string | null;
}

// Token lives in memory only (not localStorage/sessionStorage) to limit XSS exposure.
// Consequence: a page reload requires signing in again. Documented in docs/release/known-limitations.md.
let session: Session = { token: "", tenantId: null };

export function setSession(next: Session): void {
  session = next;
}
export function getSession(): Session {
  return session;
}
export function clearSession(): void {
  session = { token: "", tenantId: null };
}

/** The server sends `message` as a string for domain errors but as a nested object/array for
 * field-validation errors (e.g. {"non_field_errors": ["..."]}). Flatten to readable text. */
export function flattenMessage(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(flattenMessage).filter(Boolean).join(" ");
  if (typeof value === "object" && value !== null) {
    return Object.entries(value as Record<string, unknown>)
      .map(([field, v]) => {
        const text = flattenMessage(v);
        return field === "non_field_errors" || field === "detail" ? text : `${field}: ${text}`;
      })
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

async function parseError(response: Response): Promise<ApiError> {
  let code = "error";
  let message = `Request failed (${response.status}).`;
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "error" in body) {
      const err = (body as { error: { code?: unknown; message?: unknown } }).error;
      if (typeof err.code === "string") code = err.code;
      const flat = flattenMessage(err.message);
      if (flat) message = flat;
    } else if (typeof body === "object" && body !== null && "detail" in body) {
      message = String((body as { detail: unknown }).detail);
    }
  } catch {
    /* non-JSON error body: keep the generic message */
  }
  return new ApiError(response.status, code, message);
}

async function request<T>(
  method: "GET" | "POST",
  path: string,
  body?: unknown,
  opts: { tenant?: boolean; auth?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.auth !== false && session.token) headers["Authorization"] = `Bearer ${session.token}`;
  if (opts.tenant !== false && session.tenantId) headers["X-Tenant-ID"] = session.tenantId;
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "network", "Cannot reach the server. Check your connection and retry.");
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// ---- Contracts (mirror docs/api/openapi.yaml; decimals arrive as strings) ----
export interface TenantRef {
  id: string;
  name: string;
  slug: string;
}
export interface Me {
  email: string;
  is_platform_operator: boolean;
  tenants: TenantRef[];
}
export interface Company {
  id: string;
  name: string;
  [k: string]: unknown;
}
export interface Branch {
  id: string;
  name: string;
  code?: string;
  company?: string;
  [k: string]: unknown;
}
export interface Uom {
  id: string;
  code: string;
  name: string;
}
export interface Product {
  id: string;
  company: string;
  sku: string;
  name: string;
  uom: string;
  tax_code: string | null;
  sale_price: string;
  is_service: boolean;
  is_active: boolean;
}
export interface Warehouse {
  id: string;
  company: string;
  branch: string;
  code: string;
  name: string;
}
export interface StockRow {
  warehouse: string;
  sku: string;
  qty: string;
  avg_cost: string;
  value: string;
}
export interface ReceiptResult {
  id: string;
  qty: string;
  unit_cost: string;
  kind: string;
  replayed: boolean;
}
export interface InvoiceRow {
  id: string;
  number: string;
  date: string;
  channel: string;
  status: string;
  total: string;
  amount_paid: string;
  fiscal_status: string;
}
export interface FiscalStatus {
  efris_maturity: string;
  note: string;
}

export interface NewProduct {
  company: string;
  sku: string;
  name: string;
  uom: string;
  sale_price: string;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ token: string; expires_at: string }>(
      "POST",
      "/auth/login/",
      { email, password },
      { auth: false, tenant: false },
    ),
  logout: () => request<void>("POST", "/auth/logout/", undefined, { tenant: false }),
  me: () => request<Me>("GET", "/me/", undefined, { tenant: false }),
  companies: () => request<Company[]>("GET", "/companies/"),
  branches: () => request<Branch[]>("GET", "/branches/"),
  uoms: () => request<Uom[]>("GET", "/uoms/"),
  products: () => request<Product[]>("GET", "/products/"),
  createProduct: (p: NewProduct) => request<Product>("POST", "/products/", p),
  warehouses: () => request<Warehouse[]>("GET", "/warehouses/"),
  stock: () => request<StockRow[]>("GET", "/inventory/stock/"),
  receiveStock: (r: {
    warehouse: string;
    product: string;
    qty: string;
    unit_cost: string;
    idempotency_key: string;
  }) => request<ReceiptResult>("POST", "/inventory/receipts/", r),
  invoices: () => request<InvoiceRow[]>("GET", "/sales/invoices/"),
  fiscalStatus: () => request<FiscalStatus>("GET", "/fiscal/status/"),
};
