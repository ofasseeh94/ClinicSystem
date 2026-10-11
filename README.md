# Pediatric Clinic System

Repository: [ofasseeh94/ClinicSystem](https://github.com/ofasseeh94/ClinicSystem).
Full design: [design baseline and navigation map](docs/design/README.md).

Private pediatric clinic EMR scaffold. Current milestone: M0 (repository foundation).
No clinical features are implemented. Use synthetic data only; this is not ready for patient care.

## Repository map

Start with [docs index](docs/00-index.md) and the [step-by-step build journal](docs/build-journal.md). Web client: `apps/web`; API: `services/api`;
shared contracts and deterministic clinical rules: `packages`; migrations and synthetic seeds: `db`.

## Local setup

Prerequisites: Node.js 22+, Python 3.12+, and Docker Compose for PostgreSQL.

1. Copy `.env.example` to `.env` and set a local database password.
2. Run `docker compose --env-file .env -f infrastructure/compose.yaml up -d`.
3. Run `npm install` at the repository root.
4. Run `python -m venv .venv`, then `.venv/Scripts/python -m pip install -e "services/api[dev]"` on Windows.
5. Run `npm run dev:web` for the frontend foundation page.
6. Run `.venv/Scripts/python -m uvicorn clinic_api.main:app --app-dir services/api/src --reload` for the API health endpoint.

On POSIX systems use `.venv/bin/python` in place of `.venv/Scripts/python`.
The API currently has no database connection or patient endpoints. Configuration does not imply functionality.

## Checks

`python scripts/check_structure.py` validates the scaffold.
`python -m unittest discover -s tests/unit` runs foundation tests.
`npm run typecheck` and `npm run build` validate the web client after install.
`.venv/Scripts/python -m ruff check services/api` checks Python style after install.
CI runs these checks plus the API smoke test. OpenAPI baseline: `docs/api/openapi.yaml`.

## Next milestone

M1: authenticated registry, transactional patient/guardian registration, search, versioned forms,
and audit. Managed identity, hosting region, production security and clinical validation remain open.

## Workspace filesystem limitation

The initial dependency install in this Google Drive-mounted workspace failed with npm EBADF/EPERM write errors; Python virtual environment bootstrapping also stalled. Use a local NTFS checkout for dependency installation and builds, excluding `.venv` and `node_modules` when copying. The generated npm lockfile is available for `npm ci`. Structure checks pass, but frontend build and API smoke checks have not been verified locally. Docker was not available, so PostgreSQL startup was not verified.

## Source control and documentation

The `main` branch holds the source scaffold and all supplied design documentation. Start with the documentation index and build journal before editing. After each build step, update the journal with changed files, reasoning, verification and modification guidance. `.env`, virtual environments, build outputs and dependency folders are excluded by `.gitignore`. This repository is public; only source, configuration examples and synthetic-data design material belong here.
