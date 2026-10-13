# Clinic data dictionary — implemented foundations

Unit 04A / migration [005](../../db/migrations/005_medication_foundation.sql): `medication_catalog`
stores immutable catalog/source content versions, independent optimistic review revisions and review
actor/time/reason. `medication_statements` stores immutable reported use/source/time/optional links and
correction chains. Catalog identity review does not approve clinical rules; no prescriptions/dose rules exist.

Source of truth: PostgreSQL migrations [001](../../db/migrations/001_registry.sql), [002](../../db/migrations/002_background_v2.sql) and [003](../../db/migrations/003_encounters.sql).
All patient-domain tables carry `clinic_id`; composite foreign keys prevent cross-clinic links.
Migration [004](../../db/migrations/004_documents_investigations.sql) adds documents/investigations.
Patient record IDs are server generated; encounters/documents/orders/results use validated UUID retry IDs.
Timestamps are UTC `timestamptz`, rendered in Africa/Cairo.

| Table | Stored data and invariants |
| --- | --- |
| patients | UUID; unique immutable clinic code; original Arabic/English names; normalized search names; DOB anchor/precision/source; growth-reference sex including unknown; explicit allergy review; active/archived status; optimistic version; creation/update actor/time. At least one name required. |
| contacts | UUID; original/normalized guardian name; E.164 phone; verification date (initially absent); attribution/time. Phone match does not imply identity equivalence. |
| patient_contacts | Scoped patient/contact link; relation; unverified/verified/revoked authority state; attribution/time. New links start unverified. No authority-verification API yet. |
| patient_aliases | UUID; original and normalized alias; scoped patient link; creator/time. Profile replacement retains old aliases in audit snapshots. |
| allergies | UUID; substance/reaction; active or superseded state; creator/time; scoped patient link. Unknown/no-known reviews are distinct patient states. |
| form_definitions | Global shared form key and integer version; immutable JSON schema; publication time. v1 background and additive v2 ventilation field. |
| form_responses | UUID; scoped patient; exact form key/version; immutable JSON answers; author/time. Omitted fields mean not recorded. Read responses include the exact saved form version's schema. |
| audit_events | Ordered sequence; UUID; clinic/actor/action/record; JSON snapshot payload; previous/event SHA-256 hashes; UTC creation time. Append-only UPDATE/DELETE triggers; staff changes store reasons and before/after values. |
| idempotency_keys | Clinic/actor/request UUID key; request hash; original creation response; patient link; creation time. Same key/data returns original response, changed data is rejected. |
| schema_migrations | Migration filename, SHA-256 checksum and applied time; applied scripts cannot silently change. |
| encounters | Migration 003: clinic-scoped dated visit, reason, consent context, saved birth context, structured note and raw measurement JSON, draft/review/signed/cancelled state, version, actors/timestamps, signing/cancellation and immutable creation replay. Signed/cancelled rows cannot be changed or deleted. |
| encounter_addenda | Migration 003: immutable reason/text, signing actor/server time, request hash and scoped signed-parent FK. Appends without changing the parent's version. |
| documents | Migration 004: patient/optional encounter link, immutable title/category/source/date and uploader, lifecycle/version, original MIME/size/SHA-256, AES-GCM encrypted bytea, scanning detail and withdrawal reason. Content cannot be replaced/deleted; plaintext key stays outside DB/Git. |
| document_scans | Immutable document-linked scanner state/detail, attributed actor/server time. Raw daemon text is not retained. |
| investigation_orders | Patient/encounter-scoped request with original test name/indication/priority, versioned status, actors/times and cancellation reason. Completed/cancelled requests immutable. |
| investigation_results | Immutable source-attributed reported text/units/ranges/interpretation, collection time, optional order/document and superseded-result links, creator/time/reason. Unique supersedes link prevents branching corrections. |
| patient_code_sequence | Generates globally unique `PC-000001` style codes; gaps after rollbacks are expected. |

## Explicit unknown values

DOB precision: exact/estimated/month/year. DOB source: guardian/document/imported/unknown.
Growth reference sex: female/male/unknown. Allergy review: unknown/not_assessed/no_known/known.
Known allergies require at least one substance/reaction pair; other review states cannot include allergy rows.
Uncertain DOB retains a dated anchor but suppresses exact-age presentation. Numeric form fields can be omitted;
NICU and ventilation allow yes/no/unknown/not_recorded. These are recorded history, not clinical diagnoses.

## Future changes

Add ordered migrations, regenerate OpenAPI and update schema-driven UI/contracts/tests together.
Publish a new form version rather than editing v1/v2 or existing answers. No automatic patient merge,
clinical-event deletion, verified guardian-consent model or source-verified rule data exists yet.
