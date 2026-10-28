# Vision

*Status: draft from Blueprint §2 — awaiting owner approval (Stage 0). Canonical source: `docs/ASG_ERP_MASTER_BLUEPRINT.md` §2. If this file and the Blueprint differ, record the conflict (see `CLAUDE.md`).*

ASG ERP is a configurable business-management platform with its own code, UX and identity. It connects stock, sales, accounting, HR, POS, reporting, multi-company/branch operation, projects, fleet, documents/approvals, and a controlled app marketplace in one system. Initial market: **Uganda**. It must suit small businesses and scale towards larger organisations without a separate product per size.

## Goals (Blueprint §2.1)
Secure multi-tenant platform · tenant → companies → branches with scoped permissions · independently installable apps · web/desktop/Android/iOS via a shared API and design system · reliable offline capture and sync · configurable templates/branding · Uganda-specific configuration · trustworthy accounting/inventory/payments/approvals/audit · controlled marketplace · repeatable upgrades, backup, restore, monitoring.

## Non-goals for first release (Blueprint §2.2)
Full parity with mature ERPs · microservices without evidence · unrestricted third-party code in core · claiming regulatory compliance before verification · treating offline transactions as server-accepted or fiscalised · every industry template before core workflows are reliable.

## Success measures (Blueprint §2.3)
Tracked as requirements in `REQUIREMENTS.md` (NFR-*) and evidenced in `PROGRESS.md`.

## Not yet defined (owner input needed)
Target customers and first template (D-001), personas/priority workflows, MVP boundary — see `docs/product/decision-register.md`.
