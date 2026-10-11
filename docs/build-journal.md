# Build journal and maintenance guide

This is the living, step-by-step explanation of how the Pediatric Clinic System is built.
Update this document after every build step, including partial or blocked steps. Read it alongside
[the documentation index](00-index.md) when returning to the project.

## Current position

Last updated: 2026-10-11 (clinic timezone: Africa/Cairo).
Repository: local Git repository at `G:/My Drive/Work/Pediatrics/ClinicSystem-AI`.
Remote repository: [ofasseeh94/ClinicSystem](https://github.com/ofasseeh94/ClinicSystem), public.
The initial source/documentation upload completed; `main` tracks `origin/main`. See Step 004.
Current milestone: M0 foundation established; full environment validation remains incomplete.
Patient registration and all clinical features remain planned.

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
