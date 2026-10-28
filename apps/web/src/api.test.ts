import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, clearSession, flattenMessage, setSession } from "./api";
import { mockApi, TENANT_A } from "./test-utils";

beforeEach(() => clearSession());
afterEach(() => vi.restoreAllMocks());

describe("api client (mocked fetch: verifies the request contract, not the live server)", () => {
  it("sends bearer token and X-Tenant-ID on tenant-scoped calls", async () => {
    const calls = mockApi({ "GET /products/": [] });
    setSession({ token: "tok", tenantId: TENANT_A.id });
    await api.products();
    expect(calls[0]?.headers["Authorization"]).toBe("Bearer tok");
    expect(calls[0]?.headers["X-Tenant-ID"]).toBe(TENANT_A.id);
  });

  it("does not send credentials or tenant on login", async () => {
    const calls = mockApi({ "POST /auth/login/": { token: "t", expires_at: "x" } });
    setSession({ token: "stale", tenantId: TENANT_A.id });
    await api.login("a@b.test", "pw");
    expect(calls[0]?.headers["Authorization"]).toBeUndefined();
    expect(calls[0]?.headers["X-Tenant-ID"]).toBeUndefined();
  });

  it("maps the server error envelope to ApiError", async () => {
    mockApi({
      "GET /inventory/stock/": Response.json(
        { error: { code: "forbidden", message: "Nope." } },
        { status: 403 },
      ),
    });
    await expect(api.stock()).rejects.toMatchObject({
      status: 403,
      code: "forbidden",
      message: "Nope.",
    });
  });

  it("reports a network failure distinctly", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("down"));
    const err = await api.stock().catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 0, code: "network" });
  });
});

describe("flattenMessage / validation errors (shape observed from the live server)", () => {
  it("turns a nested field-validation envelope into readable text", async () => {
    mockApi({
      "POST /products/": Response.json(
        {
          error: {
            code: "invalid",
            message: { non_field_errors: ["The fields company, sku must make a unique set."] },
          },
        },
        { status: 400 },
      ),
    });
    setSession({ token: "t", tenantId: TENANT_A.id });
    const err = await api
      .createProduct({ company: "c", sku: "S", name: "n", uom: "u", sale_price: "1" })
      .catch((e: unknown) => e);
    expect(err).toMatchObject({
      status: 400,
      code: "invalid",
      message: "The fields company, sku must make a unique set.",
    });
  });

  it("prefixes per-field errors with the field name", () => {
    expect(flattenMessage({ sku: ["This field is required."], sale_price: ["Invalid."] })).toBe(
      "sku: This field is required. sale_price: Invalid.",
    );
    expect(flattenMessage("plain")).toBe("plain");
    expect(flattenMessage(null)).toBe("");
  });
});
