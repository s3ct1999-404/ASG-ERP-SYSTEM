/** Display mapping for fiscal states. The server decides state; the UI only labels it.
 * Honesty rule (Blueprint 7.6): a simulated acceptance must never read as URA acceptance. */
export interface FiscalLabel {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  note?: string;
}

const MAP: Record<string, FiscalLabel> = {
  NOT_REQUIRED: { label: "Not required", variant: "outline" },
  PENDING_FISCALISATION: { label: "Pending fiscalisation", variant: "secondary" },
  SUBMITTED: { label: "Submitted - awaiting confirmation", variant: "secondary" },
  FISCALISED: { label: "Fiscalised (authority confirmed)", variant: "default" },
  SIMULATED_ACCEPTED: {
    label: "SIMULATED - not URA accepted",
    variant: "outline",
    note: "Produced by the local simulator. No submission reached URA.",
  },
  REJECTED: { label: "Rejected", variant: "destructive" },
  FAILED_RETRYABLE: { label: "Failed - will retry", variant: "destructive" },
  NEEDS_ATTENTION: { label: "Needs attention", variant: "destructive" },
};

export function fiscalLabel(status: string): FiscalLabel {
  return MAP[status] ?? { label: `Unknown (${status})`, variant: "destructive" };
}
