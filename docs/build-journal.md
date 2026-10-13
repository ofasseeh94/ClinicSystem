# Build journal and maintenance guide

This is the living, step-by-step explanation of how the Pediatric Clinic System is built.
Update this document after every build step, including partial or blocked steps. Read it alongside
[the documentation index](00-index.md) when returning to the project.

## Current position

Last updated: 2026-10-13 (clinic timezone: Africa/Cairo).
Repository: local Git repository at `G:/My Drive/Work/Pediatrics/ClinicSystem-AI`.
Remote repository: [ofasseeh94/ClinicSystem](https://github.com/ofasseeh94/ClinicSystem), public.
The initial source/documentation upload completed; `main` tracks `origin/main`. See Step 004.
Current milestone: M3 / Unit 03 documents/investigations tested with synthetic data. M0 local build blockers resolved.
Registry, encounters, raw measurements, encrypted attachments and investigation records are implemented.
Live malware scanning, later clinical modules and production gates remain open.

## Step 001 — Establish the repository foundation

Date: 2026-10-10. Outcome: scaffold created; dependency-dependent checks blocked.

### Purpose and scope

Establish navigable folders, documented architecture boundaries, development configuration and
checks before building individual features. The supplied engineering specification informed the
layout. Its embedded instructions were treated as reference material, while the user's request
established the scope: repository structure before feature development.

### How it was built

1. Inspected the project folder: it was empty, with no previous prototype or Git history.
2. Selected React/TypeScript with Vite for the browser, FastAPI/Python for the API, and PostgreSQL
   for future persistence. Recorded the choice and its reversal implications in ADR-001.
3. Created separate locations for browser code, backend code, contracts, deterministic clinical
   rules, migrations, synthetic seeds, tests, infrastructure and documentation.
4. Added a static browser foundation page and a process-health API endpoint. Neither reads or
   writes patient information. The health response does not verify database connectivity.
5. Added a local PostgreSQL Compose service with a persistent named volume, a loopback-only
   port binding and a required environment password. No application schema was created.
6. Added npm workspace scripts, Python package configuration, an npm lockfile, ignored generated
   files, editor conventions, a structure validator, foundation tests and a CI definition.
7. Initialized local Git. No remote, push, commit or production deployment was performed.
8. Ran available checks and documented installation failures without marking the milestone complete.

### What exists and where to change it

| Concern | Files / folders | How to modify later |
| --- | --- | --- |
| Setup and commands | [README](../README.md), [.env.example](../.env.example) | Keep setup instructions aligned with configuration; keep secrets out of Git. |
| Project working rules | [AGENTS.md](../AGENTS.md) | Maintain documentation and validation obligations for future contributors. |
| Architecture and stack | [Overview](architecture/overview.md), [ADR-001](architecture/adr/001-stack.md) | Record a superseding ADR for a stack change; preserve the original decision. |
| Web entry point | [main.tsx](../apps/web/src/main.tsx), [style.css](../apps/web/src/style.css), [web package](../apps/web/package.json), [tsconfig](../apps/web/tsconfig.json) | Add feature components and routes here; validate types and build after changes. |
| API entry point | [main.py](../services/api/src/clinic_api/main.py), [pyproject](../services/api/pyproject.toml) | Introduce domain routes/services in separate modules; keep entry point small. |
| API contract | [OpenAPI](api/openapi.yaml) | Update when routes or schemas change; current hand-maintained baseline documents only health. |
| Database | [Compose](../infrastructure/compose.yaml), [migrations](../db/migrations/README.md), [seeds](../db/seeds/README.md) | Introduce ordered application migrations with M1; no patient tables currently exist. |
| Contracts and clinical engines | [Contracts](../packages/shared-contracts/README.md), [Rules](../packages/clinical-rules/README.md) | Reserved locations only; introduce reviewed implementations with corresponding milestones. |
| Checks and CI | [Structure checker](../scripts/check_structure.py), [unit test](../tests/unit/test_structure.py), [health test](../tests/integration/test_health.py), [CI](../.github/workflows/ci.yml) | Update required paths and checks when architecture changes; CI is defined but has not run remotely. |
| Status and evidence | [Milestones](milestones.md), [test report](test-report.md), [change log](change-log.md) | Keep completed, blocked, planned and validated work distinct. |

### Verification and limitations

Passed: structure validator and one foundation unit test. npm lockfile generation completed;
its audit reported zero vulnerabilities at that resolution, which is not a security sign-off.

Blocked: npm dependency extraction encountered EBADF/EPERM errors on the Google Drive-mounted
folder, so frontend typecheck/build could not execute successfully. Python virtual-environment
bootstrap stalled, so backend lint and API integration tests remain unverified. Docker was
unavailable, so PostgreSQL startup remains unverified. Remote CI has not run.

Evidence and exact commands are in [the validation report](test-report.md) and the README.
No application migration, patient record, authentication, clinical calculation or production release exists.

### Recovery and revisiting this step

Prefer a local NTFS checkout for development dependencies, preserving source and `.git` while
excluding generated `.venv` and `node_modules`. Install using the lockfile, then run the documented
checks. Record results here before changing M0 to complete. Do not delete database volumes to
resolve dependency installation errors. No application data migration needs rollback at this stage.

## Step 002 — Establish ongoing build documentation

Date: 2026-10-10. Outcome: documentation workflow established.

Created this journal and the reusable entry template below. Linked it from README and the docs
index. Updated AGENTS.md to require an entry after every build step, with a user-facing link in
the completion report. Added the journal to the required-path validator and recorded this change
in the change log. This documents the existing scaffold; it adds no application features.

Validation: structure validator and foundation unit test rerun successfully after these changes.
No migration or runtime configuration changed.

## Step 003 — Create the GitHub repository (pending sign-in)

Date: 2026-10-11. Outcome: blocked before repository creation; no remote changes made.

Purpose: create a private `ClinicSystem-AI` repository on the user's GitHub account and
connect it to this local project. The connected GitHub plugin verified account `ofasseeh94`.
Its available tools do not include repository creation. GitHub CLI is unavailable locally.
Opened GitHub's repository creation page in the in-app browser; GitHub redirected to sign-in.
The connector's authenticated session does not sign in the browser automatically.

Files changed: this journal and [change log](change-log.md). No code, schema or configuration changed.
Verification: `git remote -v` showed no remote; the browser displayed the GitHub sign-in page.
No repository URL is claimed, and no files have been uploaded or committed.

Next: user signs in to GitHub in the open browser, then create the private repository, verify its
URL, configure the local remote and record the outcome here. This entry must be followed by a
completion entry when creation succeeds. No migration or recovery action is needed.

## Step 004 — Link the design and source to GitHub

Date: 2026-10-11. Outcome: completed; 44 source/configuration/documentation files published.
Purpose: place the complete existing scaffold and supplied design baseline
in the user's `ofasseeh94/ClinicSystem` repository. This supersedes the Step 003 sign-in blocker.
Repository metadata verified the account, push permission, public visibility and default branch `main`.
The repository had no branch refs before upload.

### Implementation and exact changes

- Added [the engineering master specification](design/Pediatric_Clinic_Engineering_Master_Spec_v1.md), preserved byte-for-byte from the supplied Markdown file.
- Added [design navigation](design/README.md), linking baseline sections to maintained documents and identifying the unavailable original DOCX blueprint.
- Updated [README](../README.md) and [docs index](00-index.md) with repository and design links.
- Updated this journal and [change log](change-log.md) with the repository setup step.
- Added [.gitattributes](../.gitattributes) to keep source line endings consistent and preserve the imported baseline bytes.
- Added the design documents to [structure validation](../scripts/check_structure.py).
- Uploaded the existing source/configuration/documentation inventory from Steps 001–002; generated dependencies, local environment files and Git internals are excluded.

The baseline includes the complete supplied module design, data catalog, proposed APIs,
safety boundaries and milestone plan. Working documents accurately describe the implemented M0 subset.
No individual clinic feature or application migration was added.

### Verification and maintenance

Structure check and the foundation unittest pass. The imported specification hash is recorded
in its design README. Publication verified: local HEAD and remote `main` both resolved to
`877e2b8bf5ce05f8fb2cc6be46302740b4d195bc` after the initial push. The GitHub connector
retrieved `docs/design/README.md` successfully. Initial commit: [877e2b8](https://github.com/ofasseeh94/ClinicSystem/commit/877e2b8bf5ce05f8fb2cc6be46302740b4d195bc).
The follow-up documentation commit records this result. Remote Actions status has not been verified. Existing dependency-install and database validation limits
remain recorded in the test report; uploading source does not resolve them.

To revise earlier parts, follow the design navigation map and Step 001 file guide, change the
owning source/documentation together, and append a new journal entry. Commit subsequent changes
and push `main` to `origin`. Do not rewrite the imported specification to conceal historical decisions.
Git history preserves the initial scaffold; no database rollback is needed for this documentation step.

## Step 005 — Resolve local development dependencies and PostgreSQL

Date: 2026-10-11. Outcome: local build and actual PostgreSQL testing enabled.

Moved npm dependencies and the Python venv to local NTFS under `%LOCALAPPDATA%/ClinicSystem`;
installed pinned dependencies and EDB PostgreSQL 17.11 binaries, initialized a password-protected
loopback cluster, and created separate synthetic-development and `_test` databases.
Credentials remain in ignored local configuration/runtime files and are not uploaded.
Docker remains unavailable; PostgreSQL itself was exercised rather than substituting SQLite or memory storage.

Added sync/start/stop scripts with hidden server processes and PID/start-time validation; the sync
script excludes dependencies/secrets. Captured setup in README and the development runbook.
Typecheck/build and database startup succeeded. Earlier M0 dependency blockers are resolved locally.
No real-data backup/restore or production deployment was performed.

## Step 006 — Build Unit 01: the patient registry

Date: 2026-10-11. Outcome: TESTED for synthetic development.

### What was completed and how

1. Added ordered checksum-verified PostgreSQL migrations for patients, contacts, scoped links,
   aliases, allergy records, form definitions/responses, replay keys and audit events.
2. Split the backend into configuration/auth/errors/database and registry route/schema/service/query/form/audit modules.
3. Added clinic/role enforcement and explicit local development authentication; production refuses local keys
   and verifies managed RS256 JWT claims. Live provider/MFA/browser OIDC remain a release gate.
4. Added quick registration in one transaction, unique clinic codes, masked name/alias/guardian/phone search,
   deliberate duplicate review, and request keys that prevent duplicate creates on retries.
5. Added ETag/version-controlled corrections with reasons and before/after audit snapshots.
6. Added explicit allergy states and immutable background form v1/v2 responses. New history appends a record,
   and the overview receives the exact saved form schema. Numeric entry bounds are not clinically validated.
7. Built a responsive staff registry, registration/optional background form and patient overview with
   later-module empty states. Arabic text is preserved and normalized only for search.
8. Added generated OpenAPI YAML/JSON, shared frontend types, PostgreSQL/security/contract tests,
   Playwright acceptance, synthetic screenshots and a PostgreSQL-enabled GitHub workflow.
9. Updated design/data/workflow/setup docs and added a complete unit maintenance guide and file manifest.

### Verification, revisiting and limits

20 Python tests pass; Ruff/structure and TypeScript/Vite build pass; the real browser workflow passes.
Desktop/mobile screenshots were inspected. Added a regression check rejecting nonfinite numeric background input. Initial browser-test failures exposed a test selector issue
and duplicate synthetic names on reruns; the fixture now uses distinct names and tests the duplicate path deliberately.
Tests also caught a phone-mask text encoding error, which was fixed while preserving original patient names.

See [Unit 01 guide](units/01-patient-registry.md) for the exact changed-file manifest, data flow and
modification map; [test report](test-report.md) for environment/results; [ADR-002](architecture/adr/002-registry-boundaries.md)
for persistence/search/auth/history choices. The two migrations are now applied locally and must never be rewritten.
Changes require additive migrations/form versions; destructive rollback is not provided. Production restore drills,
restricted DB roles, external audit integrity, distributed limits, managed sign-in and clinical/privacy sign-offs remain open.

Publication: [initial Unit 01 commit](https://github.com/ofasseeh94/ClinicSystem/commit/1c21c1f79a83acfb3bad7693744d2131e016a22b).
The first remote CI run passed build/backend checks but its browser step failed because nested npm scripts
forwarded the port argument as a Vite directory. CI now launches Vite directly with the intended root/port;
the [follow-up run](https://github.com/ofasseeh94/ClinicSystem/actions/runs/38123538692) passed completely for
[commit ef6379f](https://github.com/ofasseeh94/ClinicSystem/commit/ef6379ffa3ea117a0c99318c7288db8881d6606d).
The local project and GitHub main were verified to match after publication. A documentation-only follow-up
records these results; see the validation report.

Next planned unit: encounters, signed note lifecycle/addenda and dated measurements. No prescribing,
growth/vaccine recommendations, documents, parent messaging or AI was added in this unit.

## Step 007 — Build Unit 02: encounters, signatures and dated measurements

Date: 2026-10-11. Outcome: TESTED for synthetic development; extends Step 006.

### Purpose and implementation sequence

1. Read the existing journal, architecture/data dictionary and M2 design to preserve registry IDs,
   historical forms, clinic isolation and atomic audit. Selected encounters as the next planned unit.
2. Added migration 003 for versioned encounter snapshots and separate signed addenda. PostgreSQL
   triggers prevent final-record editing/deletion and addenda editing/deletion; unsigned parents reject addenda.
3. Added validated backend schemas, clinic-scoped transaction/query services and endpoints for create,
   timeline/read, draft replacement, status transitions and addenda. Reused authenticated actors and audit.
4. Added mandatory version/If-Match checks, UUID creation/addendum replay and transaction locks.
   Draft changes retain before/after audit snapshots. Signing requires complete narrative/review acknowledgment.
5. Captured DOB precision/source/patient version at visit creation and calculated age on the Cairo visit
   date. Later profile corrections preserve this context; uncertain dates suppress exact age.
6. Added dated raw kg/cm measurements with source/position/technique/equipment, finite positive validation
   and displayed age at measurement from saved birth context. No medical reference calculations added.
7. Built the patient Encounters tab: paginated timeline, note/measurement editor, review/sign/cancel,
   immutable read view and signed addendum. Added deliberate discard/reload and unsaved navigation warnings.
8. Regenerated API contracts; added PostgreSQL lifecycle/security/concurrency/date/immutability tests and
   a desktop/mobile browser acceptance flow. Updated the documentation and complete maintenance manifest.

### Exact changes and modification guide

The complete changed-file manifest, ownership map and design/recovery explanation are in
[Unit 02](units/02-encounters.md). Change validations in encounter schemas, transitions/transactions
in the service, endpoint behavior in routes, permissions in auth, and entry/navigation behavior in
Encounters/PatientOverview/App. Keep shared types, generated contracts, tests and docs synchronized.
The design rationale is [ADR-003](architecture/adr/003-encounter-lifecycle.md); staff steps are in
[the encounter workflow](workflows/encounters.md).

### Verification and resolved findings

29 Python tests pass against actual PostgreSQL 17.11; Ruff, structure, TypeScript and production
bundle checks pass. Both Playwright workflows pass (registry and encounter), including saving raw
measurements, signing, addendum preservation and reopening. Desktop/mobile screenshots inspected.
Tests caught and resolved timezone formatting differences in replay responses, review-selector labels,
and a save-completion race that could reset a newly entered reason. Inputs now pause while saving.
The browser test uses accessible textbox roles for disabled note fields. The upstream TestClient
deprecation warning remains; no production/clinical/backup-restore validation performed.

### Data impact, limits and next prerequisites

Migration 003 is additive and applied to local development and test databases. Registry rows and
forms remain intact. Do not rewrite applied SQL; use later migrations. No destructive down migration
exists. Stop writes and use a verified restore procedure if recovery is required; restore remains untested.
Draft note/measurement versions live in immutable audit snapshots, rather than a dedicated history UI.
Addenda preserve the signed parent's version and append text corrections; structured measurement corrections
are deferred. Technical input limits are not clinically approved plausibility rules. Consent text does
not verify authority, and signing is staff attestation without cryptographic document signatures.
Managed identity/MFA, production security/operations and clinical/privacy sign-off remain open.

Next planned unit: private documents/investigations foundation (M3), with storage and upload protections
defined before handling attachments. Clinical engines still require source-verified reference data.
Publication: [Unit 02 implementation commit 25bc78e](https://github.com/ofasseeh94/ClinicSystem/commit/25bc78e7f179d53a864d13fb28118ff24d777c8b).
Publication/remote verification results are recorded in the validation report after push.
The initial remote run passed build/lint and 28 tests but failed generated-contract equality because
Python 3.12 and 3.14 use different default HTTP 422 descriptions. Added explicit encounter error
descriptions and regenerated contracts; strict contract checking remains enabled.
Completed remote verification: [run 38126496635](https://github.com/ofasseeh94/ClinicSystem/actions/runs/38126496635)
passed the full workflow for [corrected commit ff9e96e](https://github.com/ofasseeh94/ClinicSystem/commit/ff9e96e0e849d0ce7c20700d343e27c9aa3502a7).
This includes all 29 Python tests, frontend checks and both browser workflows. The local preview
was updated and readiness passed; the existing development access key was preserved.
A documentation-only follow-up records this evidence and the repository synchronization result.

## Step 008 — Restore the clinic preview on its own port

Date: 2026-10-13. Outcome: local preview restored; supersedes the development web address used in Steps 005–007.

Purpose: the old `http://127.0.0.1:5173/` address was serving the Momentum productivity tool.
HTTP inspection confirmed that page title, while the clinic API/database were stopped. Restarted
the existing local PostgreSQL cluster and clinic servers; retained the existing data and access key.
Changed the clinic web address to `http://127.0.0.1:5174/`. The API remains on 8000.

Exact changes: `apps/web/vite.config.ts` sets loopback port 5174 with strict binding;
`scripts/start-dev.ps1` checks/launches/reports 5174; `playwright.config.ts` tests that default;
`.github/workflows/ci.yml` launches the same port; `README.md` and
`docs/operations/runbooks/development.md` document the correct address and recovery;
`docs/change-log.md` and this journal record the repair. Earlier historical port references are preserved.

Modification guide: change Vite, launcher, browser-test default and CI port together if another
address is required. Sync source to the NTFS build before launch. Strict binding prevents Vite
from silently selecting another port. Start the preserved database cluster before starting the API.

Verification: HTTP title on 5174 is Pediatric Clinic; `/ready` returns ok; 5173 still serves Momentum.
Both browser acceptance flows pass on 5174 (registry and encounters), repository structure and its
unit test pass, and Git diff whitespace check passes. Initial acceptance checks ran before startup
completed and failed connection checks; rerunning after readiness succeeded. No full backend or
production suite was required for this port-only change. Remote CI results for this repair are not yet verified.

Data/recovery impact: no migration or clinical record change. PostgreSQL restarts reuse the existing
cluster; no database/volume was deleted. Stopping the preview uses recorded clinic process identities.
Clinical/production release gates and the next planned M3 unit remain as recorded in Step 007.

## Step 009 — Build Unit 03: documents and investigations

Date: 2026-10-13. Outcome: TESTED for synthetic development; extends Steps 006–008.

### What was built and how

1. Read prior build decisions and baseline M3; retained clinic-scoped IDs, historical records and atomic audit.
2. Added migration 004 for encrypted document content/metadata/lifecycle, append-only scan evidence,
   versioned investigation requests and immutable results with correction chains.
3. Chose bounded PostgreSQL ciphertext for the first private storage backend. AES-GCM protects original
   bytes with clinic/document context; SHA-256 records the file hash. Metadata and audit remain DB records.
4. Added static PDF/PNG/JPEG format checks and 10 MiB streaming limits, PDF page/active-content restrictions,
   image validation/pixel caps and safe parser diagnostics. Added a ClamAV streaming adapter with fail-closed
   quarantine behavior and bounded network deadlines. Local synthetic mode is separately labeled and forbidden in production.
5. Added authenticated 60-second actor/clinic/patient/document/hash tickets, issued/used in POST bodies.
   Retrieval rechecks state/permissions and verifies encrypted bytes/hash under the lifecycle transaction lock.
6. Added patient/encounter-scoped request creation, status transitions with If-Match, attributed reported
   results and immutable corrections. UUID replay prevents duplicate creates; corrections retain prior values.
7. Built Documents/Investigations forms, lists, source links, memory-only viewer/download, withdrawal/rescan,
   reason prompts, pagination and navigation safeguards. Added a clearly fictional sample file.
8. Updated config/launcher/dependency pins/CI for stable private keys and explicit synthetic test state.
   Generated contracts and added real PostgreSQL, scanner-protocol/encryption/parser and browser regression checks.
9. Updated design/navigation/data/workflow/runbook/status docs and the complete Unit 03 maintenance guide.

### File changes, design decisions and modification guide

The exact changed-file manifest is in [Unit 03](units/03-documents-investigations.md), alongside the
ownership map and detailed source-to-screen flow. [ADR-004](architecture/adr/004-private-documents.md)
records why this increment uses encrypted DB storage, explicit scanner states and ticketed retrieval.
Adjust fields in records schemas/shared types/screens, transactions in records service, byte/scanner/crypto
policy in files, permissions in auth and persistence through a new migration. Update contracts/tests/docs together.
The [staff workflow](workflows/documents-investigations.md) describes usage independently of implementation.

### Verification and corrections

39 Python tests pass using PostgreSQL 17.11; Ruff/structure, TypeScript/Vite and all three browser flows pass.
Inspected document-viewer/mobile screenshots. Browser tests exercise source-file upload/view/download,
linked result/correction, completion and withdrawal, plus previous units. Fixed a test locator for prefilled
textarea content; repaired mobile action overflow and added an overflow assertion. Ciphertext tampering,
wrong context/key, ticket expiry/scope, invalid/active/oversized input, role/patient/clinic isolation, quarantine,
replay, version conflict and historical corrections were checked. Scanner network fixtures emulate verdicts;
no live ClamAV engine/signature database was tested. Detailed results are in [the test report](test-report.md).

### Migration, key preservation, limitations and recovery

After updating/restarting the preview, an earlier synthetic attachment was retrieved and its hash
verified using the preserved key. The final local browser run passed all three workflows.

Migration 004 is additive and applied locally to development/test DBs. Previous migrations were not changed.
Document metadata is recorded before content; an interrupted upload may leave a pending slot to retry or
withdraw. Original encrypted content/metadata and results cannot be overwritten/deleted. Withdrawal blocks
new retrieval, but does not recall bytes already downloaded. No destructive rollback exists.

Preserve the existing document key outside Git; losing/replacing it prevents historical decryption.
Restore requires a verified DB backup and that key; full restore/rotation is untested. Object storage,
managed keys, parser process isolation/resource control, production scanner deployment/signatures/private
transport, quotas/retention, restricted roles, live identity and privacy/clinical sign-off remain release gates.
Recent-item selectors show 20; full historical selectors are deferred while paginated/API records remain.
No OCR/AI extraction, external lab messaging, automatic interpretation, clinical reference ranges or prescribing added.

Next: baseline M4 medication knowledge/drug safety foundation needs verified clinical/catalog sources
and independent validation before dose calculations or prescribing can be enabled. Publication evidence
will be recorded after the repository push and remote checks.

## Template for every future build step

Append a numbered entry; retain prior entries. If an earlier implementation is changed, add a new
entry referencing the original step and explain what supersedes it. Correct factual errors visibly.

- **Date, milestone and outcome:** completed, partial or blocked; include commit/PR link when available.
- **Purpose:** user-visible result and acceptance criteria.
- **Implementation:** explain the sequence, data flow and design choices in plain language.
- **Exact changes:** link each changed file or a complete change manifest, and explain its role.
- **Modification guide:** where to adjust behavior, validation, UI, configuration and contracts later.
- **Data impact:** tables, migrations, compatibility, preservation of historical records and recovery plan.
- **Validation:** commands actually run, their results and checks not run; link evidence.
- **Limitations and decisions:** unresolved issues, approvals or sources required, and ADR references.
- **Next step:** remaining work and prerequisites; do not mark planned work as implemented.

## Foundation file inventory

This inventory describes source/configuration files after Step 002. Generated dependency folders,
Git internals and local environment files are excluded.

- [.editorconfig](../.editorconfig)
- [.env.example](../.env.example)
- [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- [.gitignore](../.gitignore)
- [AGENTS.md](../AGENTS.md)
- [apps/web/index.html](../apps/web/index.html)
- [apps/web/package.json](../apps/web/package.json)
- [apps/web/src/main.tsx](../apps/web/src/main.tsx)
- [apps/web/src/style.css](../apps/web/src/style.css)
- [apps/web/tsconfig.json](../apps/web/tsconfig.json)
- [db/migrations/README.md](../db/migrations/README.md)
- [db/seeds/README.md](../db/seeds/README.md)
- [docs/00-index.md](../docs/00-index.md)
- [docs/api/openapi.yaml](../docs/api/openapi.yaml)
- [docs/architecture/adr/001-stack.md](../docs/architecture/adr/001-stack.md)
- [docs/architecture/overview.md](../docs/architecture/overview.md)
- [docs/change-log.md](../docs/change-log.md)
- [docs/clinical/rules-register.md](../docs/clinical/rules-register.md)
- [docs/clinical/safety-cases.md](../docs/clinical/safety-cases.md)
- [docs/data/data-dictionary.md](../docs/data/data-dictionary.md)
- [docs/data/er-diagram.md](../docs/data/er-diagram.md)
- [docs/milestones.md](../docs/milestones.md)
- [docs/operations/runbooks/development.md](../docs/operations/runbooks/development.md)
- [docs/test-report.md](../docs/test-report.md)
- [docs/workflows/registration.md](../docs/workflows/registration.md)
- [infrastructure/compose.yaml](../infrastructure/compose.yaml)
- [package-lock.json](../package-lock.json)
- [package.json](../package.json)
- [packages/clinical-rules/README.md](../packages/clinical-rules/README.md)
- [packages/shared-contracts/README.md](../packages/shared-contracts/README.md)
- [README.md](../README.md)
- [scripts/check_structure.py](../scripts/check_structure.py)
- [services/api/pyproject.toml](../services/api/pyproject.toml)
- [services/api/src/clinic_api/__init__.py](../services/api/src/clinic_api/__init__.py)
- [services/api/src/clinic_api/main.py](../services/api/src/clinic_api/main.py)
- [tests/clinical/README.md](../tests/clinical/README.md)
- [tests/e2e/README.md](../tests/e2e/README.md)
- [tests/integration/test_health.py](../tests/integration/test_health.py)
- [tests/security/README.md](../tests/security/README.md)
- [tests/unit/test_structure.py](../tests/unit/test_structure.py)
- [docs/build-journal.md](build-journal.md) (this document)
