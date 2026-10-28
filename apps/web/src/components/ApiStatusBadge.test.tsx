import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiStatusBadge } from "./ApiStatusBadge";

afterEach(() => vi.restoreAllMocks());

describe("ApiStatusBadge", () => {
  it("reports API ok when readiness returns ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ status: "ok" }));
    render(<ApiStatusBadge />);
    expect(await screen.findByText("API status: ok")).toBeInTheDocument();
  });

  it("reports unavailable when the API says so", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ status: "unavailable" }, { status: 503 }),
    );
    render(<ApiStatusBadge />);
    expect(await screen.findByText("API status: unavailable")).toBeInTheDocument();
  });

  it("reports unreachable when the network fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("network"));
    render(<ApiStatusBadge />);
    expect(await screen.findByText("API status: unreachable")).toBeInTheDocument();
  });
});
