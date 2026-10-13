# Change log

## 2026-10-13 — Custom local development access key

Allowed custom development keys of at least eight characters and configured the user's requested
key in ignored local settings. Default generated keys remain random; production still rejects
development authentication. No actual access key was added to repository documentation.

## 2026-10-13 — Unit 03: documents and investigations

Added migration 004, encrypted private attachments with original hashes and bounded format validation,
explicit scanner/quarantine/synthetic states, authenticated short-lived retrieval tickets and withdrawal.
Added investigation orders, versioned status, attributed reported results and immutable correction chains.
Built Documents/Investigations interfaces, source-linked viewer/history and a fictional sample attachment;
updated contracts, dependencies, tests, CI setup and maintenance/recovery documentation. Live ClamAV,
key management/rotation, private object storage, parser isolation and restore remain production gates.

## 2026-10-13 — Restore clinic preview

Assigned the clinic preview port 5174 after port 5173 was serving the productivity tool.
Aligned Vite strict binding, Windows launcher, browser tests, CI and setup documentation.
Restarted existing local database/API/web processes and verified the clinic title, readiness and
both browser workflows. Preserved existing data and development access key; no migration changed.

## 2026-10-11 — Unit 02: encounters

Added migration 003, clinic/role-scoped dated encounters, saved birth-date/age context, structured
notes and raw measurements, optimistic draft edits, review/sign/cancel lifecycle, database protection
for final snapshots and immutable signed addenda. Added retry-safe create/addendum IDs, responsive
timeline/editor with unsaved guards, generated contracts, PostgreSQL/browser tests and complete
Unit 02 maintenance documentation. No clinical calculation or production release added.

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
