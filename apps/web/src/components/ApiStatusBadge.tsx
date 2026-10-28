import { useEffect, useState } from "react";
import { type ApiStatus, fetchApiStatus } from "@/api";

export function ApiStatusBadge() {
  const [status, setStatus] = useState<ApiStatus | "checking">("checking");
  useEffect(() => {
    const controller = new AbortController();
    void fetchApiStatus(controller.signal).then((result) => {
      if (!controller.signal.aborted) setStatus(result);
    });
    return () => controller.abort();
  }, []);
  return (
    <p role="status" className="text-xs text-muted-foreground">
      API status: {status}
    </p>
  );
}
