import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { clearSession } from "./api";
import { mockApi, TENANT_A, TENANT_B } from "./test-utils";

// Component tests over a mocked fetch: they check UI behaviour and the request contract.
// They are NOT proof that the live API works (see docs/release/verification-report.md).

const ME = { email: "owner@alpha.test", is_platform_operator: false, tenants: [TENANT_A] };
const FISCAL = {
  efris_maturity: "SIMULATED_AND_TESTED",
  note: "Simulator only. No real URA submission has occurred.",
};
const base = {
  "GET /health/ready/": { status: "ok" },
  "POST /auth/login/": { token: "tok", expires_at: "2099-01-01T00:00:00Z" },
  "GET /me/": ME,
  "GET /fiscal/status/": FISCAL,
  "GET /companies/": [{ id: "c1", name: "Alpha Co" }],
  "GET /branches/": [{ id: "b1", name: "Main", code: "MAIN" }],
};

function renderApp(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
async function signIn(user = userEvent.setup()) {
  await user.type(await screen.findByLabelText("Email"), "owner@alpha.test");
  await user.type(screen.getByLabelText("Password"), "pw");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  return user;
}

beforeEach(() => clearSession());
afterEach(() => vi.restoreAllMocks());

describe("sign-in", () => {
  it("shows the login screen first, with the product name", async () => {
    mockApi(base);
    renderApp();
    expect(screen.getByText("ASG ERP")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
    await screen.findByText("API status: ok");
  });

  it("shows the server's message for bad credentials and stays signed out", async () => {
    mockApi({
      ...base,
      "POST /auth/login/": Response.json(
        { error: { code: "invalid_credentials", message: "Invalid credentials." } },
        { status: 401 },
      ),
    });
    renderApp();
    await signIn();
    expect(await screen.findByText("Invalid credentials.")).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Main" })).not.toBeInTheDocument();
  });

  it("signs in, loads the organisation, and shows the truthful EFRIS banner", async () => {
    const calls = mockApi(base);
    renderApp();
    await signIn();
    expect(await screen.findByRole("navigation", { name: "Main" })).toBeInTheDocument();
    expect(await screen.findByText("Alpha Co")).toBeInTheDocument();
    const banner = await screen.findByTestId("efris-banner");
    expect(banner).toHaveTextContent("SIMULATED_AND_TESTED");
    expect(banner).toHaveTextContent(/No real URA submission/);
    const orgCall = calls.find((c) => c.path === "/companies/");
    expect(orgCall?.headers["X-Tenant-ID"]).toBe(TENANT_A.id);
  });

  it("tells a user with no memberships they have no access, and loads no business data", async () => {
    const calls = mockApi({ ...base, "GET /me/": { ...ME, tenants: [] } });
    renderApp();
    await signIn();
    expect(await screen.findByText("No organisation access")).toBeInTheDocument();
    expect(calls.some((c) => c.path === "/companies/")).toBe(false);
  });
});

describe("tenant switching", () => {
  it("only offers the user's own tenants and sends the chosen one", async () => {
    const calls = mockApi({ ...base, "GET /me/": { ...ME, tenants: [TENANT_A, TENANT_B] } });
    renderApp();
    const user = await signIn();
    const select = await screen.findByLabelText("Organisation", { selector: "select" });
    expect(
      within(select)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Alpha Ltd", "Bravo Ltd"]);
    await user.selectOptions(select, TENANT_B.id);
    await waitFor(() => {
      const last = [...calls].reverse().find((c) => c.path === "/companies/");
      expect(last?.headers["X-Tenant-ID"]).toBe(TENANT_B.id);
    });
  });
});

describe("stock receipt idempotency", () => {
  const stockRoutes = {
    ...base,
    "GET /warehouses/": [
      { id: "w1", company: "c1", branch: "b1", code: "MAIN", name: "Main store" },
    ],
    "GET /products/": [
      {
        id: "p1",
        company: "c1",
        sku: "SUG1",
        name: "Sugar",
        uom: "u1",
        tax_code: null,
        sale_price: "5000.00",
        is_service: false,
        is_active: true,
      },
    ],
    "GET /inventory/stock/": [],
  };

  async function fill(user: ReturnType<typeof userEvent.setup>) {
    await user.type(await screen.findByLabelText("Quantity"), "10");
    await user.type(screen.getByLabelText("Unit cost"), "3000");
  }

  it("reuses the same idempotency key when retrying after a failure, then renews it after success", async () => {
    let n = 0;
    const calls = mockApi({
      ...stockRoutes,
      "POST /inventory/receipts/": () => {
        n += 1;
        return n === 1
          ? Response.json({ error: { code: "x", message: "Temporary failure." } }, { status: 503 })
          : Response.json(
              {
                id: "m1",
                qty: "10.0000",
                unit_cost: "3000.0000",
                kind: "receipt",
                replayed: false,
              },
              { status: 201 },
            );
      },
    });
    renderApp("/stock");
    const user = await signIn();
    await fill(user);
    await user.click(screen.getByRole("button", { name: "Receive stock" }));
    expect(await screen.findByText("Temporary failure.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Receive stock" }));
    expect(await screen.findByText(/Received 10\.0000/)).toBeInTheDocument();
    const posts = calls.filter((c) => c.method === "POST" && c.path === "/inventory/receipts/");
    expect(posts).toHaveLength(2);
    const k1 = (posts[0]?.body as { idempotency_key: string }).idempotency_key;
    const k2 = (posts[1]?.body as { idempotency_key: string }).idempotency_key;
    expect(k1).toBe(k2);

    // A new logical receipt after a confirmed success must get a NEW key.
    await fill(user);
    await user.click(screen.getByRole("button", { name: "Receive stock" }));
    await waitFor(() =>
      expect(
        calls.filter((c) => c.method === "POST" && c.path === "/inventory/receipts/"),
      ).toHaveLength(3),
    );
    const posts3 = calls.filter((c) => c.method === "POST" && c.path === "/inventory/receipts/");
    const k3 = (posts3[2]?.body as { idempotency_key: string }).idempotency_key;
    expect(k3).not.toBe(k2);
  });

  it("says plainly when the server reports a replay (nothing added twice)", async () => {
    mockApi({
      ...stockRoutes,
      "POST /inventory/receipts/": Response.json(
        { id: "m1", qty: "10.0000", unit_cost: "3000.0000", kind: "receipt", replayed: true },
        { status: 200 },
      ),
    });
    renderApp("/stock");
    const user = await signIn();
    await fill(user);
    await user.click(screen.getByRole("button", { name: "Receive stock" }));
    expect(
      await screen.findByText(/already recorded; nothing was added twice/),
    ).toBeInTheDocument();
  });

  it("keeps the submit button disabled for invalid quantities", async () => {
    mockApi(stockRoutes);
    renderApp("/stock");
    const user = await signIn();
    await user.type(await screen.findByLabelText("Quantity"), "0");
    await user.type(screen.getByLabelText("Unit cost"), "10");
    expect(screen.getByRole("button", { name: "Receive stock" })).toBeDisabled();
  });
});

describe("permission handling and fiscal honesty", () => {
  it("shows 'Not permitted' (not a generic failure) on 403", async () => {
    mockApi({
      ...base,
      "GET /sales/invoices/": Response.json(
        { error: { code: "permission_denied", message: "no" } },
        { status: 403 },
      ),
    });
    renderApp("/invoices");
    await signIn();
    expect(await screen.findByText("Not permitted")).toBeInTheDocument();
  });

  it("labels a simulated acceptance as NOT URA accepted in the invoice list", async () => {
    mockApi({
      ...base,
      "GET /sales/invoices/": [
        {
          id: "i1",
          number: "INV-1",
          date: "2026-10-28",
          channel: "invoice",
          status: "posted",
          total: "100.00",
          amount_paid: "0.00",
          fiscal_status: "SIMULATED_ACCEPTED",
        },
      ],
    });
    renderApp("/invoices");
    await signIn();
    expect(await screen.findByText("INV-1")).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED - not URA accepted/)).toBeInTheDocument();
    expect(screen.queryByText(/^Fiscalised/)).not.toBeInTheDocument();
  });
});
