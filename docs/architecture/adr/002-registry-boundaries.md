# ADR-002: Registry persistence, access and history

Status: Accepted for synthetic development; production release gated
Date: 2026-10-11. Owner: project maintainer.

Decision: direct parameterized Psycopg PostgreSQL queries behind separate routes, service, repository,
validation, form and audit modules. Patient/guardian/alias/allergy/form writes and audit append share one
transaction. A clinic-scoped advisory transaction lock protects duplicate review, revisions, idempotency
and the audit hash chain. Sequence-assigned codes are unique; rolled-back transactions may leave code gaps.

Search uses `POST /v1/patients/search` rather than the baseline's proposed GET query so names and phones
stay out of URLs, browser history and ordinary access logs. Read routes expose only opaque record IDs.
Search phones are masked. Staff record access and searches are audited; search text is not retained.

Development auth is an explicit local token with synthetic clinic/actor identity and admin permissions.
Production refuses it and validates managed RS256 JWTs with issuer, audience, expiry, subject, clinic and roles.
Live IdP/MFA setup and a browser OIDC flow remain required; local access is not a production identity model.

Contacts are normalized and linked relationally. Matching phones do not merge contacts or establish authority.
This slice creates a contact per registration; deliberate shared-contact management is deferred.
Registry corrections replace the editable profile but retain before/after audit snapshots. Known allergies
are superseded rather than erased. Background definitions/responses and audit events reject UPDATE/DELETE.
Publishing new forms uses additive migrations; there is no form-admin UI yet.

Alternatives: ORM, in-memory demo, SQLite, automatic guardian merge and URL-based search.
Rejected as unnecessary abstraction for this slice, insufficient durability, or incompatible privacy/history behavior.

Impact: baseline field schemas enforce technical entry bounds but are not clinically validated screening rules.
Production privilege separation, external audit anchors, distributed rate limits and restore drills are open.
The per-clinic write lock favors consistency over high write throughput; revisit before multi-clinic scaling.

Validation: PostgreSQL transactions, parallel idempotent creates, optimistic conflicts, form-version preservation,
masked Arabic/English searches, JWT verification, RBAC and cross-clinic denial. See test report.
Recovery: preserve applied SQL checksums. Back up before changes; never rewrite applied files or destructively
reset a clinic database. New versions/migrations are the default correction mechanism.
