# Local development

Stack: Django 5.2 LTS + DRF + PostgreSQL 16 (API), React + TypeScript on Vite (web). See `docs/adr/0002-technology-stack.md`.
All commands run from the repository root unless stated. Placeholders only — never commit real secrets.

## Prerequisites
Python 3.12 · Node.js 22+ and npm · PostgreSQL 16 (via Docker Compose below, or your own instance).

## 1. Environment
```bash
cp .env.example .env
# Edit .env: set SECRET_KEY (e.g. python3 -c "import secrets; print(secrets.token_urlsafe(50))")
# and DB_PASSWORD. For local development you may set DEBUG=true.
```
`.env` is git-ignored. The API refuses to start without `SECRET_KEY`.

## 2. Database
```bash
docker compose up -d db          # local PostgreSQL bound to 127.0.0.1 only
```
Without Docker, create a PostgreSQL 16 role/database matching `DB_*` in `.env`.

## 3. API
```bash
cd services/api
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements/dev.txt
set -a && . ../../.env && set +a          # export .env into this shell
python manage.py migrate
python manage.py runserver                # http://localhost:8000/api/v1/health/live/
```
`runserver` is development only; the production server is a deployment decision (not yet made).

## 4. Web
```bash
cd apps/web
npm ci
npm run dev                               # http://localhost:5173 (proxies /api to :8000)
```

## Verification commands (what CI runs)
API (`cd services/api`, venv active, `.env` exported, PostgreSQL running):
```bash
ruff check .
ruff format --check .
mypy .
python manage.py makemigrations --check --dry-run
python -m pytest
pip install pip-audit && pip-audit -r requirements/dev.txt --no-deps --disable-pip
```
Web (`cd apps/web`):
```bash
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
npm audit --omit=dev --audit-level=high      # blocking
npm audit                                    # visibility only (see PROGRESS.md R-008)
```

## API contract
`docs/api/openapi.yaml` is generated and **must match the code** (a test enforces it). After changing endpoints:
```bash
cd services/api && python manage.py spectacular --validate --file ../../docs/api/openapi.yaml
```
Review the diff as an API contract change.

## Dependencies
- API: edit `services/api/requirements/base.in`, rebuild the pins in a clean venv (`pip freeze`), update `base.txt`/`dev.txt`, run all checks. Django stays on the 5.2 LTS line until an ADR/task changes it.
- Web: `npm install --save-exact`; prefer releases at least 14 days old (`--before=<date>`); commit `package-lock.json`.

## Troubleshooting
- `ImproperlyConfigured: SECRET_KEY…` → `.env` not exported into your shell (step 3).
- `DisallowedHost` → add the host to `ALLOWED_HOSTS` in `.env`.
- Readiness returns 503 → PostgreSQL is not reachable with the `DB_*` values; check the logs (JSON, with `request_id`).
