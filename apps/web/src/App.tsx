import { useEffect, useState } from "react";
import { type ApiStatus, fetchApiStatus } from "./api";

export function App() {
  const [status, setStatus] = useState<ApiStatus | "checking">("checking");

  useEffect(() => {
    const controller = new AbortController();
    void fetchApiStatus(controller.signal).then((result) => {
      if (!controller.signal.aborted) setStatus(result);
    });
    return () => controller.abort();
  }, []);

  return (
    <main>
      <h1>ASG ERP</h1>
      <p role="status">API status: {status}</p>
    </main>
  );
}
