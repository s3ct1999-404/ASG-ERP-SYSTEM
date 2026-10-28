import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

afterEach(() => vi.restoreAllMocks());

describe("App", () => {
  it("shows the product name", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ status: "ok" }));
    render(<App />);
    expect(screen.getByRole("heading", { name: "ASG ERP" })).toBeInTheDocument();
    // Let the pending status update settle so it does not leak outside the test.
    await screen.findByText("API status: ok");
  });

  it("reports API ok when readiness returns ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ status: "ok" }));
    render(<App />);
    expect(await screen.findByText("API status: ok")).toBeInTheDocument();
  });

  it("reports unavailable when the API says so", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ status: "unavailable" }, { status: 503 }),
    );
    render(<App />);
    expect(await screen.findByText("API status: unavailable")).toBeInTheDocument();
  });

  it("reports unreachable when the network fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("network"));
    render(<App />);
    expect(await screen.findByText("API status: unreachable")).toBeInTheDocument();
  });
});
