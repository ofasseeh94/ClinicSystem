# Unit 01 — Patient registry: implementation and maintenance guide

Built: 2026-10-11. Status: tested for synthetic development; production gates remain open.
Repository: [ClinicSystem](https://github.com/ofasseeh94/ClinicSystem).

## What this unit does

A staff user can search, register and reopen a patient; record a guardian contact and aliases;
distinguish unknown/unassessed/no-known/known allergy history; add optional birth/medical background;
review possible duplicates; correct details with an audit reason; and preserve earlier form responses.
Arabic/English names and international phones are validated and searchable. Unique patient codes
are assigned by PostgreSQL. A saved patient survives a browser reload and new staff session.

## How the pieces connect

1. `App.tsx` opens an in-memory staff session, retrieves masked patient search results and selects a record.
2. `PatientForm.tsx` collects quick details and optional schema-driven history. Retries reuse a request UUID
   when the payload is unchanged. Corrections send the loaded version in `If-Match`.
3. `api.ts` sends bearer-authenticated requests through the same-origin `/api` proxy. It reports failures
   without claiming unsaved data was stored. Search terms travel in JSON bodies, not URLs.
4. `auth.py` resolves the staff actor, clinic and roles. Development has one explicitly synthetic admin;
   production verifies managed RS256 JWTs and cannot accept a development key.
5. `routes.py` accepts typed requests; `schemas.py` checks identity, DOB, phone and allergy states.
6. `service.py` performs permission, version, duplicate and replay checks inside a clinic-locked transaction.
7. `repository.py` uses parameterized clinic-scoped SQL for patient/contact/alias/allergy/form persistence.
8. `forms.py` validates each answer against a published version. Old definitions and responses are immutable.
9. `audit.py` appends attributed hash-linked snapshots in the same transaction; read access is also recorded.
10. `PatientOverview.tsx` renders the persisted patient and each response's exact historical form schema.
    Later clinical modules display explicit empty states rather than made-up records or calculations.

## Where to adjust things later

| Requested change | Primary location | Also update |
| --- | --- | --- |
| Required patient/contact fields | registry/schemas.py and PatientForm.tsx | Shared TypeScript contract, OpenAPI, migrations if persisted, validation and browser tests |
| Arabic normalization or phone rules | registry/normalization.py | Search/duplicate tests and original-value preservation |
| Search behavior/pagination | registry/repository.py, routes.py and App.tsx | Privacy contract, query tests and performance indexes if needed |
| Duplicate policy | repository.duplicates and service.create | ADR-002, duplicate-review UI and concurrent/replay acceptance tests |
| Permissions or staff identity | auth.py and config.py | Security tests; configured IdP claims; production browser login before deployment |
| Patient corrections/history | service.update, audit.py and PatientForm.tsx | Optimistic-lock tests and data-lifecycle documentation |
| Background fields | New ordered migration publishing a new form version | Form fixtures, data dictionary, selected form version in UI and history tests |
| Visual layout | apps/web/src/style.css and owning UI component | Typecheck/build, browser workflow and desktop/mobile screenshots |
| API shapes | schemas.py, routes.py, registry.ts | Run scripts/export-openapi.py and contract tests |
| Setup and runtime | config.py, infrastructure/compose.yaml and scripts | README/runbook, CI and real startup/shutdown verification |

Paths under `registry/` are inside `services/api/src/clinic_api/registry`.
Do not edit applied migrations 001/002 or alter an existing published form. Add a new migration/version.
No arbitrary field publishing screen is implemented; schema-driven fields are published through migrations.

## Data preservation and recovery

Quick registration, guardian link, optional background, aliases/allergies, replay key and audit share one
PostgreSQL transaction. Invalid background or a duplicate conflict leaves no partial patient.
Code sequence gaps are expected after rollbacks and are not reused. Identity changes advance the record
version and retain before/after snapshots. Allergies are superseded; previous aliases remain in audit history.
Form definitions/responses and audit rows reject ordinary UPDATE/DELETE.

This is not protection against a database superuser: production needs restricted database credentials,
external audit integrity checks and tested backups. No destructive rollback script is supplied.
Use a pre-change backup and tested restore plan before a real deployment; none has been clinically released.

## Verification evidence

19 Python tests pass on local PostgreSQL 17.11; TypeScript and Vite build pass; Ruff and structure checks pass.
One Playwright workflow passes against live API/web servers and captures desktop/mobile screenshots.
Tests cover synthetic siblings, duplicate review, uncertain DOB, allergy states, Arabic/English/alias search,
masked phones, invalid forms with atomic rollback, concurrent retries, ETag conflicts, schema drift,
immutable history, clinic isolation, role denial, production JWT checks and secret-safe configuration repr.
See [validation report](../test-report.md) for commands and environment caveats.

## What remains outside this unit

Live managed IdP/MFA and browser OIDC login; guardian contact sharing/authority verification and consent;
form-admin publishing; large-registry indexing; distributed rate limits; production DB privilege isolation,
TLS/encryption, session revocation, externally anchored audits, restore drills and privacy/clinical sign-off.
Form entry bounds have not received clinical validation. Free-text reported medication/condition history
is not a coded clinical problem list or a prescription. No encounters, orders, dose engine, growth engine,
vaccine recommendations, documents, notifications or AI are implemented.

Next planned unit: encounters, versioned notes/signatures/addenda and dated measurements.

## Complete source/documentation change manifest

The manifest below includes every tracked modification and new source file for Steps 005–006,
excluding ignored local credentials, dependencies, runtime logs and test outputs.

- [.env.example](../../.env.example)
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- [.gitignore](../../.gitignore)
- [README.md](../../README.md)
- [apps/web/src/App.tsx](../../apps/web/src/App.tsx)
- [apps/web/src/BackgroundFields.tsx](../../apps/web/src/BackgroundFields.tsx)
- [apps/web/src/PatientForm.tsx](../../apps/web/src/PatientForm.tsx)
- [apps/web/src/PatientOverview.tsx](../../apps/web/src/PatientOverview.tsx)
- [apps/web/src/api.ts](../../apps/web/src/api.ts)
- [apps/web/src/format.ts](../../apps/web/src/format.ts)
- [apps/web/src/main.tsx](../../apps/web/src/main.tsx)
- [apps/web/src/style.css](../../apps/web/src/style.css)
- [apps/web/vite.config.ts](../../apps/web/vite.config.ts)
- [db/migrations/001_registry.sql](../../db/migrations/001_registry.sql)
- [db/migrations/002_background_v2.sql](../../db/migrations/002_background_v2.sql)
- [db/migrations/README.md](../../db/migrations/README.md)
- [db/seeds/README.md](../../db/seeds/README.md)
- [docs/00-index.md](../../docs/00-index.md)
- [docs/api/openapi.yaml](../../docs/api/openapi.yaml)
- [docs/architecture/adr/002-registry-boundaries.md](../../docs/architecture/adr/002-registry-boundaries.md)
- [docs/architecture/overview.md](../../docs/architecture/overview.md)
- [docs/build-journal.md](../../docs/build-journal.md)
- [docs/change-log.md](../../docs/change-log.md)
- [docs/data/data-dictionary.md](../../docs/data/data-dictionary.md)
- [docs/data/er-diagram.md](../../docs/data/er-diagram.md)
- [docs/milestones.md](../../docs/milestones.md)
- [docs/operations/runbooks/development.md](../../docs/operations/runbooks/development.md)
- [docs/screenshots/README.md](../../docs/screenshots/README.md)
- [docs/screenshots/unit-01-mobile.png](../../docs/screenshots/unit-01-mobile.png)
- [docs/screenshots/unit-01-overview.png](../../docs/screenshots/unit-01-overview.png)
- [docs/screenshots/unit-01-registry.png](../../docs/screenshots/unit-01-registry.png)
- [docs/test-report.md](../../docs/test-report.md)
- [docs/units/01-patient-registry.md](../../docs/units/01-patient-registry.md)
- [docs/workflows/registration.md](../../docs/workflows/registration.md)
- [package-lock.json](../../package-lock.json)
- [package.json](../../package.json)
- [packages/shared-contracts/README.md](../../packages/shared-contracts/README.md)
- [packages/shared-contracts/openapi.json](../../packages/shared-contracts/openapi.json)
- [packages/shared-contracts/registry.ts](../../packages/shared-contracts/registry.ts)
- [playwright.config.ts](../../playwright.config.ts)
- [pytest.ini](../../pytest.ini)
- [scripts/check_structure.py](../../scripts/check_structure.py)
- [scripts/export-openapi.py](../../scripts/export-openapi.py)
- [scripts/migrate.py](../../scripts/migrate.py)
- [scripts/start-dev.ps1](../../scripts/start-dev.ps1)
- [scripts/stop-dev.ps1](../../scripts/stop-dev.ps1)
- [scripts/sync-local.ps1](../../scripts/sync-local.ps1)
- [scripts/wait-ready.py](../../scripts/wait-ready.py)
- [services/api/pyproject.toml](../../services/api/pyproject.toml)
- [services/api/requirements-dev.lock](../../services/api/requirements-dev.lock)
- [services/api/src/clinic_api/auth.py](../../services/api/src/clinic_api/auth.py)
- [services/api/src/clinic_api/config.py](../../services/api/src/clinic_api/config.py)
- [services/api/src/clinic_api/database.py](../../services/api/src/clinic_api/database.py)
- [services/api/src/clinic_api/errors.py](../../services/api/src/clinic_api/errors.py)
- [services/api/src/clinic_api/main.py](../../services/api/src/clinic_api/main.py)
- [services/api/src/clinic_api/registry/__init__.py](../../services/api/src/clinic_api/registry/__init__.py)
- [services/api/src/clinic_api/registry/audit.py](../../services/api/src/clinic_api/registry/audit.py)
- [services/api/src/clinic_api/registry/forms.py](../../services/api/src/clinic_api/registry/forms.py)
- [services/api/src/clinic_api/registry/normalization.py](../../services/api/src/clinic_api/registry/normalization.py)
- [services/api/src/clinic_api/registry/repository.py](../../services/api/src/clinic_api/registry/repository.py)
- [services/api/src/clinic_api/registry/routes.py](../../services/api/src/clinic_api/registry/routes.py)
- [services/api/src/clinic_api/registry/schemas.py](../../services/api/src/clinic_api/registry/schemas.py)
- [services/api/src/clinic_api/registry/service.py](../../services/api/src/clinic_api/registry/service.py)
- [tests/conftest.py](../../tests/conftest.py)
- [tests/e2e/registry.spec.ts](../../tests/e2e/registry.spec.ts)
- [tests/integration/test_health.py](../../tests/integration/test_health.py)
- [tests/integration/test_registry.py](../../tests/integration/test_registry.py)
- [tests/security/test_registry_security.py](../../tests/security/test_registry_security.py)
- [tests/unit/test_contracts.py](../../tests/unit/test_contracts.py)
- [tests/unit/test_registry_validation.py](../../tests/unit/test_registry_validation.py)
- [tests/unit/test_structure.py](../../tests/unit/test_structure.py)
