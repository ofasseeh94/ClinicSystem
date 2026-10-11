# Change log

## 2026-10-11 — Unit 01: patient registry

Resolved Drive dependency issues with a local NTFS runtime and tested actual PostgreSQL 17.11.
Added normalized registry migrations, staff auth/role checks, masked Arabic/English search, transactional
registration, duplicate review, idempotent retries, audited ETag corrections, explicit allergy states,
immutable versioned background forms and a responsive patient overview. Added generated API contracts,
20 Python tests, a browser acceptance flow, desktop/mobile screenshots, locked dependencies, launch/sync
scripts, PostgreSQL-backed CI and complete maintenance documentation. No clinical algorithms or production
release; live identity, privacy, operations and clinical gates remain open. The corrected remote
registry CI run passed PostgreSQL, build and browser checks; the validation report links the evidence.

## 2026-10-10 — M0 foundation

Established repository layout, stack ADR, frontend foundation page, health API, local PostgreSQL configuration, baseline checks and CI. No application migrations or clinical features; no migration rollback is needed.

## 2026-10-10 — Build documentation workflow

Added the step-by-step build journal with foundation implementation details and a maintenance map. Required journal updates after every build step in AGENTS.md; linked the journal from README and the docs index; included it in scaffold validation. Local repository has no remote URL.

## 2026-10-11 — GitHub repository setup pending

Verified connected GitHub account. Repository creation requires browser sign-in because the connector has no repository-creation tool and GitHub CLI is unavailable. No repository was created or files uploaded. Recorded the blocker in the build journal.

## 2026-10-11 — GitHub source and design baseline

Linked the project to ofasseeh94/ClinicSystem. Added the complete supplied engineering specification and design navigation map; updated README, documentation index, journal and structure checks. Initial publication includes source/configuration and documentation, excluding generated dependencies and secrets. No clinical features or schema changes.
