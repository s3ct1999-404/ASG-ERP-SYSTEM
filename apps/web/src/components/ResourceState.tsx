import type { ReactNode } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { Resource } from "@/lib/useResource";

/** Renders loading / error / empty states so every list page behaves the same. */
export function ResourceState<T>({
  resource,
  isEmpty,
  emptyText,
  children,
}: {
  resource: Resource<T[]>;
  isEmpty?: (d: T[]) => boolean;
  emptyText: string;
  children: (data: T[]) => ReactNode;
}) {
  if (resource.loading)
    return (
      <p role="status" className="text-sm text-muted-foreground">
        Loading...
      </p>
    );
  if (resource.error) {
    const denied = resource.error.status === 403;
    return (
      <Alert variant="destructive">
        <AlertTitle>{denied ? "Not permitted" : "Could not load data"}</AlertTitle>
        <AlertDescription>
          <p>{denied ? "Your role does not allow viewing this." : resource.error.message}</p>
          {!denied && (
            <Button size="sm" variant="outline" onClick={resource.reload}>
              Retry
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }
  const data = resource.data ?? [];
  if ((isEmpty ?? ((d: T[]) => d.length === 0))(data)) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>;
  }
  return <>{children(data)}</>;
}
