# ADR-0005: Web UI kit: shadcn/ui on Tailwind CSS v4

- Status: Accepted (owner instruction in session 2026-10-29: "use the shadcn ui tool when building the front-end"). Fulfils the deferral in ADR-0002 Decision 2 ("UI kit deferred to the first slice").
- Context: React 19 + TypeScript + Vite already chosen. The web app was a placeholder shell.
- Decision: shadcn/ui (new-york style, Tailwind v4, CSS variables, `@/` alias, `components.json` committed) with `radix-ui`, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`; `react-router-dom` for routing. All versions pinned exactly.
- Provenance of components (be exact): `button` and `input` were fetched verbatim from the shadcn v4 registry via the shadcn MCP tool (only the `cn` import alias rewritten). The shadcn tool became unavailable mid-session, so `label`, `card`, `table`, `badge`, `alert` and `select` were **written by hand following shadcn v4 conventions** (cva, `cn`, `data-slot`). `select` is a styled native `<select>`, not the Radix Select. **Follow-up:** re-fetch those six from the registry when the tool is available and diff.
- Consequences: components are owned source in `apps/web/src/components/ui/`; no runtime dependency on a hosted UI service. Business rules stay out of components (`api.ts` and the server are authoritative; `lib/fiscal.ts` only labels states).
- Security: bearer token held in memory only (not web storage) to limit XSS exposure; reload requires sign-in. Tenant switching can only select tenants returned by `/me/`.
