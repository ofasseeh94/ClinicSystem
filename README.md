# Pediatric Clinic System

Repository: [ofasseeh94/ClinicSystem](https://github.com/ofasseeh94/ClinicSystem).
[Design baseline](docs/design/README.md) · [Documentation index](docs/00-index.md) · [Build journal](docs/build-journal.md)

Units 01–03: a PostgreSQL-backed clinic record for **synthetic development data**.
Unit 04A adds reported medication history/corrections and a versioned catalog identity/source-review
foundation. Dose calculations and prescribing remain disabled; baseline M4 is not yet complete.
Register patients and guardians, search Arabic/English names and aliases, review duplicate candidates,
reopen an overview, correct identity details with a reason, and append versioned medical/birth background.
Unknown allergy history remains explicit. Open Encounters for dated visits, notes, raw measurements,
review/signing, cancellation and immutable signed addenda. Later clinical modules remain planned.
Documents supports encrypted PDF/PNG/JPEG attachments, attributed source metadata, controlled retrieval
and withdrawal. Investigations tracks requests, reported results and immutable corrections.
The local launcher uses explicit synthetic attachment mode: files are NOT malware scanned.
This is not a production medical record system; managed sign-in, security and clinical release gates remain open.

## Repository map

`apps/web`: React interface; `services/api`: FastAPI/auth/registry; `packages/shared-contracts`:
shared TypeScript types and generated OpenAPI; `db/migrations`: ordered PostgreSQL schema/form versions;
`tests`: unit, PostgreSQL integration, security and browser tests; `docs`: design and maintenance history.

## Local setup

Prerequisites: Node.js 22+, Python 3.12+ and PostgreSQL 17 (Docker Compose or local binaries).

1. Copy `.env.example` to `.env`, replace the local password, and match `DATABASE_URL` to it.
2. If using Docker, run `docker compose --env-file .env -f infrastructure/compose.yaml up -d`.
3. Install Python dependencies into a local venv:
   `python -m venv .venv`, `.venv/Scripts/python -m pip install -r services/api/requirements-dev.lock`,
   then `.venv/Scripts/python -m pip install -e services/api --no-deps`.
4. Set `DATABASE_URL` in the API process environment and run `.venv/Scripts/python scripts/migrate.py`.
5. Run `npm ci`, then `npm run dev:web`. Vite forwards `/api` to `127.0.0.1:8000`.
6. Set `APP_ENV=development` and `DEV_AUTH_TOKEN` for the API (minimum 8 characters).
   The launcher generates a long random key by default; a custom development key can be set in the ignored `.env`.
   Run `.venv/Scripts/python -m uvicorn clinic_api.main:app --app-dir services/api/src --host 127.0.0.1 --port 8000 --no-access-log`.
7. Open `http://127.0.0.1:5174` and enter the development token. The browser holds it in memory only;
   closing the session, reloading or 20 minutes of inactivity clears the browser session.

On POSIX, use `.venv/bin/python`. The API reads environment variables, not `.env` automatically.
The Windows launcher below loads `.env`. Missing database/auth configuration fails closed.

## Windows / Google Drive workspace

Dependency extraction on the Drive mount failed during M0. Keep dependencies on local NTFS:

1. Run `./scripts/sync-local.ps1` to copy source into `%LOCALAPPDATA%/ClinicSystem/build`.
2. Run `npm ci` in that build directory.
3. Create `%LOCALAPPDATA%/ClinicSystem/runtime/venv` and install the pinned Python development dependencies there.
4. Configure the repository's ignored `.env` with your PostgreSQL connection.
5. Run `./scripts/start-dev.ps1`. It applies checksum-verified migrations, generates a local development key
   if needed, and starts API/web processes hidden on loopback. Find the key in
   `%LOCALAPPDATA%/ClinicSystem/runtime/development-access-key.txt`.
6. Run `./scripts/stop-dev.ps1` to stop only the recorded API/web process trees, with process-start checks.
   Database data is preserved. Re-run the sync script after edits before rebuilding the frontend.

This workstation currently uses local PostgreSQL binaries on port 55432 and local NTFS dependencies.
Portable PostgreSQL startup/stop instructions are in the [development runbook](docs/operations/runbooks/development.md).
Do not copy `.env` or generated dependency folders into Git. The repository is public.

## Verification

- `python scripts/check_structure.py`
- `python -m ruff check --config services/api/pyproject.toml services/api scripts tests`
- `python -m pytest` (set `TEST_DATABASE_URL` to a PostgreSQL database ending in `_test`; otherwise DB tests skip)
- `npm run typecheck` and `npm run build`
- `python scripts/export-openapi.py` after API changes; the contract test detects stale published schemas
- `npx playwright install chromium`, then `npm run test:e2e` with the servers running and `DEV_AUTH_TOKEN` set

CI provisions PostgreSQL and runs the same checks plus browser acceptance. Screenshots use fictional records.
See [test report](docs/test-report.md), [Unit 01 guide](docs/units/01-patient-registry.md) and [screenshots](docs/screenshots/README.md).
The [Unit 02 guide](docs/units/02-encounters.md) explains encounter use, storage, edits and recovery.
The [Unit 03 guide](docs/units/03-documents-investigations.md) explains attachments, investigations,
scanning states and encryption-key preservation. Try the fictional sample in the Documents tab.
The [Unit 04A guide](docs/units/04-medication-foundation.md) explains medication history, catalog
review/versioning and the source/clinical prerequisites before drug calculations can be enabled.

## Production prerequisites

Production configuration refuses development keys and requires managed OIDC issuer/audience/JWKS settings.
The JWT verifier is tested; a live identity provider, MFA, browser OIDC flow, relationship permissions,
restricted database role, TLS/encryption, backup/restore drills, operational monitoring, privacy review and
clinical validation are still required before real patient data. No parent access or outbound messages exist.
