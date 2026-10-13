# Validation report

## 2026-10-13 — Unit 03 documents and investigations

| Check | Result |
| --- | --- |
| Pytest | PASS: 39 tests against PostgreSQL 17.11, including 10 new document/crypto/parser/protocol/investigation cases |
| Ruff and repository structure | PASS |
| TypeScript and Vite bundle | PASS |
| Playwright | PASS: all three workflows (registry, encounters, documents/investigations) |
| Migration 004 / readiness | PASS: applied to development/test DBs, previous checksums preserved |
| Retained attachment after restart | PASS: retrieved an earlier encrypted synthetic attachment and verified its original SHA-256 with the persisted key |
| Desktop document viewer / mobile investigations | Inspected; mobile action wrapping repaired and no-horizontal-overflow assertion added |
| Scanner protocol | PASS: controlled TCP fixtures for clean, detection, error and unexpected responses |
| Live ClamAV signature database, production, parser isolation, backup restore | NOT RUN; local synthetic attachments are explicitly unscanned |
| Remote GitHub Actions | Pending publication verification |

Commands: documented root checks, Pytest with TEST_DATABASE_URL, typecheck/build and browser acceptance
with the clinic API/web on 8000/5174. Dependencies added: pypdf 6.20.1 and Pillow 12.3.0; crypto remains
cryptography 50.0.2. Parser caps, MIME mismatch/active PDF rejection, upload size, original hash,
encrypted storage and tamper/context integrity were checked. Ticket expiry/scope/withdrawal, role and
patient/clinic boundaries, optimistic order/document transitions, replay and retained result corrections
were checked. Browser flow uploads/views/downloads, links a result, corrects it, completes an order and
withdraws the source; prior units still pass. The first new browser run found a prefilled textarea test
locator issue, fixed by using its accessible textbox role. Screenshot review caught/fixed mobile overflow.
Upstream TestClient and the pypdf active-content fixture helper produce deprecation warnings; tests pass.

The scanner fixtures do not claim actual malware detection. Ciphertext/key backup restore, real scanner
deployment/signature maintenance, quotas/retention, managed keys/rotation, parser sandboxing and live
identity remain production gates. No real patient attachments or clinical interpretation were used.

## 2026-10-11 — Unit 02 encounters

| Check | Result |
| --- | --- |
| Pytest | PASS: 29 tests using PostgreSQL 17.11, including 9 new encounter/measurement cases |
| Ruff and repository structure | PASS |
| TypeScript and Vite bundle | PASS |
| Playwright | PASS: both registry and encounter workflows |
| Migration 003 / readiness | PASS: applied locally to development/test DBs; earlier checksums preserved |
| Desktop/mobile encounter screenshots | Inspected; synthetic records only |
| Remote Actions | PASS: [corrected run 38126496635](https://github.com/ofasseeh94/ClinicSystem/actions/runs/38126496635), including all 29 Python tests, frontend checks and both browser workflows |
| Production, clinical acceptance, backup restore | NOT RUN |

Used the same local Python/Node/PostgreSQL environment and commands as Unit 01 below. New tests
exercise complete lifecycle and addenda, immutable SQL guards, stale/missing versions, review locking,
role/clinic isolation, unknown DOB, preserved birth context after correction, invalid/future dates,
nonfinite/nonpositive measurements, Cairo date boundary and concurrent edits/creation retries.
Browser acceptance enters notes/measurements, reviews/signs, appends a correction and reopens on mobile.
Initial failures were resolved: consistent UTC retry timestamps, accessible selector labels, a reason
input race while saving and the test locator for disabled fields. Upstream TestClient warning remains.
Initial remote evidence: [run 38126328625](https://github.com/ofasseeh94/ClinicSystem/actions/runs/38126328625)
passed frontend/lint and 28 tests; the contract check exposed Python-version-dependent HTTP descriptions.
Encounter routes now supply stable descriptions, preserving the strict schema equality check.
Corrected code: [ff9e96e](https://github.com/ofasseeh94/ClinicSystem/commit/ff9e96e0e849d0ce7c20700d343e27c9aa3502a7).
The successful run used Python 3.12 / Node 22 and PostgreSQL 17.11 on Linux. Local API readiness
was rechecked after updating the preview, with the existing development key preserved.

## 2026-10-11 — Unit 01 registry

| Check | Result |
| --- | --- |
| Repository structure | PASS |
| Ruff (API, scripts and Python tests) | PASS |
| Pytest unit/integration/security/contract suite | PASS: 20 tests, using actual PostgreSQL 17.11 |
| TypeScript `tsc --noEmit` | PASS |
| Vite production bundle | PASS |
| Playwright browser acceptance | PASS: one end-to-end flow, desktop and mobile screenshots |
| Migrations | PASS: checksum verification, repeated application and immutable v1/v2 history |
| Local readiness and development start/stop | PASS; PostgreSQL on 55432, API on 8000, web on 5173 |
| Remote GitHub Actions | PASS: [registry run 38123538692](https://github.com/ofasseeh94/ClinicSystem/actions/runs/38123538692), including PostgreSQL, build and browser acceptance |
| Docker Compose startup | NOT RUN: Docker unavailable locally; PostgreSQL binaries used instead |
| Production/clinical acceptance and backup restore | NOT RUN; no production readiness claimed |

Commands: `python scripts/check_structure.py`; `python -m ruff check --config services/api/pyproject.toml services/api scripts tests`;
`python -m pytest -q --tb=short` with TEST_DATABASE_URL; `npm run typecheck`; `npm run build`;
`npx playwright test` with DEV_AUTH_TOKEN and live synthetic servers. Dependencies run from local NTFS.
Python 3.14.4 and Node 24.15.0 were used locally; the successful remote CI exercised Python 3.12 / Node 22.
One upstream FastAPI/Starlette TestClient deprecation warning is present with pinned httpx; tests pass.

Screenshots: [registry](screenshots/unit-01-registry.png), [overview](screenshots/unit-01-overview.png),
[mobile](screenshots/unit-01-mobile.png). All are synthetic.

## Earlier foundation results (historical)

- PASS: repository structure validator.
- PASS: one foundation unittest.
- PASS: npm lockfile generation; npm audit reported zero vulnerabilities for that resolution.
- BLOCKED: frontend typecheck/build; dependency extraction failed with filesystem write errors.
- BLOCKED: API smoke and lint checks; virtual environment bootstrap stalled on the mounted drive.
- NOT RUN: Docker/PostgreSQL startup; Docker command unavailable.
- NOT VERIFIED: remote CI status. Repository linked and source pushed on 2026-10-11; previous report predates publication.

No application schema or patient features exist. Dependency installation and build validation remain prerequisites to completing M0.

## 2026-10-11 — Publication verification

Structure validation and the foundation unittest passed. `git diff --cached --check` passed before the initial commit. Verified remote `main` matched local commit `877e2b8bf5ce05f8fb2cc6be46302740b4d195bc`; GitHub connector retrieved the design navigation document. No runtime feature claims or clinical validation were added.
