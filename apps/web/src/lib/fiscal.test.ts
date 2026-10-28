import { describe, expect, it } from "vitest";
import { fiscalLabel } from "./fiscal";

describe("fiscalLabel", () => {
  it("never presents a simulated acceptance as authority acceptance", () => {
    const l = fiscalLabel("SIMULATED_ACCEPTED");
    expect(l.label).toMatch(/SIMULATED/);
    expect(l.label).toMatch(/not URA accepted/i);
    expect(l.label).not.toMatch(/^Fiscalised/);
  });
  it("only FISCALISED reads as fiscalised", () => {
    expect(fiscalLabel("FISCALISED").label).toMatch(/authority confirmed/);
    expect(fiscalLabel("SUBMITTED").label).toMatch(/awaiting confirmation/);
  });
  it("flags unknown server states instead of hiding them", () => {
    const l = fiscalLabel("SOMETHING_NEW");
    expect(l.label).toMatch(/Unknown/);
    expect(l.variant).toBe("destructive");
  });
});
