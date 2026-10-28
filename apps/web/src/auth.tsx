import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { api, ApiError, clearSession, getSession, setSession, type TenantRef } from "@/api";

interface AuthState {
  email: string | null;
  isPlatformOperator: boolean;
  tenants: TenantRef[];
  tenantId: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  selectTenant: (id: string) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(null);
  const [isPlatformOperator, setOperator] = useState(false);
  const [tenants, setTenants] = useState<TenantRef[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);

  const signIn = useCallback(async (e: string, password: string) => {
    const { token } = await api.login(e, password);
    setSession({ token, tenantId: null });
    try {
      const me = await api.me();
      // Only tenants the server says this user belongs to can ever be selected.
      const first = me.tenants[0]?.id ?? null;
      setSession({ token, tenantId: first });
      setEmail(me.email);
      setOperator(me.is_platform_operator);
      setTenants(me.tenants);
      setTenantId(first);
    } catch (err) {
      clearSession();
      throw err instanceof ApiError
        ? err
        : new ApiError(0, "error", "Could not load your profile.");
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      /* token may already be expired/revoked; local state is cleared regardless */
    }
    clearSession();
    setEmail(null);
    setOperator(false);
    setTenants([]);
    setTenantId(null);
  }, []);

  const selectTenant = useCallback(
    (id: string) => {
      if (!tenants.some((t) => t.id === id)) return; // never switch outside allowed scopes
      setSession({ token: getSession().token, tenantId: id });
      setTenantId(id);
    },
    [tenants],
  );

  const value = useMemo(
    () => ({ email, isPlatformOperator, tenants, tenantId, signIn, signOut, selectTenant }),
    [email, isPlatformOperator, tenants, tenantId, signIn, signOut, selectTenant],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
