# Current Sprint

> One active bounded task only. Overall status lives in `PROGRESS.md`.

## Milestone
Stage 1/2 — decisions drafted; foundation built. Implementation of tenant-scoped features is **gated on owner decisions**.

## Active task
**ASG-015 — Create Uganda compliance research records** — Status: **IN PROGRESS** (first pass complete; not finished)
Branch: `docs/asg-015-uganda-research` (local; not pushed)

## Goal
Replace assumptions with verified, source-cited, dated compliance records so tax/EFRIS/payroll/privacy rules are never implemented from memory.

## Done in the first pass (2026-10-27)
- EFRIS: URA's own public notice (Aug 2026) read in full — mandatory for VAT-registered taxpayers **and** 12 listed sectors from 1 July 2025, with turnover/rental exemptions; documents must carry the buyer's BRN/NIN/TIN; unsupported expenses lose income-tax deduction.
- Tax and data-protection records written from secondary sources/excerpts, **conflicts recorded** (FY2026/27 income-tax amendment status disputed).
- All records marked UNREVIEWED; findings annotated into D-001/D-005/D-011/D-014 and requirements CUS-001/TAX-001.

## Remaining to finish ASG-015 (acceptance: every record has an official source, date, impact, evidence, open questions, owner)
1. Read URA's current **EFRIS Handbook FY 2026/27** and technical/system-to-system documentation; answer EF-006 (is ASG required to be an accredited integrator? current offline window?).
2. Read the amendment Acts / URA guidance to resolve the TX-002 conflict; read the Data Protection and Privacy Act text and Regulations.
3. Research NSSF and other payroll obligations (PY-002).
4. Obtain qualified professional review of every record; record the reviewer and date.

## Acceptance criteria status
Not met (research incomplete, no professional review). **Do not mark DONE** until items 1–4 are complete.

## Other tasks (not active)
IN REVIEW: ASG-002 (ADR-0003 Proposed), ASG-003, ASG-004 (CI never run), ASG-014. BLOCKED: ASG-012 (needs D-005). NOT STARTED and gated: ASG-005, ASG-006, ASG-007… need ADR-0003 accepted.

## Verification plan
Docs only: secret scan, link/status checks, contract tests (`tests/contracts`, `tests/security`). Results in `NEXT_SESSION.md`.
