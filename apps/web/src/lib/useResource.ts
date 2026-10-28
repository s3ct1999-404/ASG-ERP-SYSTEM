import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/api";

export interface Resource<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

interface Settled<T> {
  id: string;
  data: T | null;
  error: ApiError | null;
}

/** Load-on-mount (and when `key` changes or `reload()` is called). `loading` is derived from
 * whether the settled result belongs to the current request, so no state is set synchronously
 * inside the effect. A result for a previous key/tick is never shown as current. */
export function useResource<T>(load: () => Promise<T>, key: string | null): Resource<T> {
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const requestId = `${key ?? ""}#${tick}`;

  useEffect(() => {
    let cancelled = false;
    load()
      .then((data) => {
        if (!cancelled) setSettled({ id: requestId, data, error: null });
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        const error = e instanceof ApiError ? e : new ApiError(0, "error", "Unexpected error.");
        setSettled({ id: requestId, data: null, error });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `load` is a stable API function; requestId captures key/tick.
  }, [requestId]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  const current = settled?.id === requestId ? settled : null;
  return {
    data: current?.data ?? null,
    error: current?.error ?? null,
    loading: current === null,
    reload,
  };
}
