/** Thin API client. Business rules never live in UI components. */
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
