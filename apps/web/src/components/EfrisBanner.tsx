import { useEffect, useState } from "react";
import { api, type FiscalStatus } from "@/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useAuth } from "@/auth";

interface Result {
  tenantId: string | null;
  status: FiscalStatus | null;
}

/** Always-visible truth about fiscalisation maturity, taken from the server (never hard-coded). */
export function EfrisBanner() {
  const { tenantId } = useAuth();
  const [result, setResult] = useState<Result | null>(null);
  useEffect(() => {
    let cancelled = false;
    api
      .fiscalStatus()
      .then((status) => !cancelled && setResult({ tenantId, status }))
      .catch(() => !cancelled && setResult({ tenantId, status: null }));
    return () => {
      cancelled = true;
    };
  }, [tenantId]);
  // Informational only: hidden while loading, for another tenant's result, or if the role lacks fiscal.read.
  if (!result || result.tenantId !== tenantId || !result.status) return null;
  return (
    <Alert data-testid="efris-banner">
      <AlertTitle>EFRIS maturity: {result.status.efris_maturity}</AlertTitle>
      <AlertDescription>{result.status.note}</AlertDescription>
    </Alert>
  );
}
