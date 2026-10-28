import { vi } from "vitest";

export interface Call {
  method: string;
  path: string;
  headers: Record<string, string>;
  body: unknown;
}
type Handler = (call: Call) => Response | Promise<Response>;

/** Mock fetch keyed by "METHOD /path" (path without /api/v1). Records every call. */
export function mockApi(routes: Record<string, Handler | Response | unknown>) {
  const calls: Call[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const path = url.replace(/^.*\/api\/v1/, "");
    const method = (init?.method ?? "GET").toUpperCase();
    const call: Call = {
      method,
      path,
      headers: (init?.headers ?? {}) as Record<string, string>,
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    };
    calls.push(call);
    const h = routes[`${method} ${path}`];
    if (h === undefined)
      return Response.json(
        { error: { code: "not_found", message: `unmocked ${method} ${path}` } },
        { status: 404 },
      );
    if (typeof h === "function") return (h as Handler)(call);
    if (h instanceof Response) return h.clone();
    return Response.json(h);
  });
  return calls;
}

export const TENANT_A = {
  id: "11111111-1111-4111-8111-111111111111",
  name: "Alpha Ltd",
  slug: "alpha",
};
export const TENANT_B = {
  id: "22222222-2222-4222-8222-222222222222",
  name: "Bravo Ltd",
  slug: "bravo",
};
