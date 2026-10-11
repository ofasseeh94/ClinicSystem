# Registry data dictionary — Unit 01

Source of truth: PostgreSQL migrations [001](../../db/migrations/001_registry.sql) and [002](../../db/migrations/002_background_v2.sql).
All patient-domain tables carry `clinic_id`; composite foreign keys prevent cross-clinic links.
UUID record IDs are server generated. Timestamps are UTC `timestamptz`, rendered in Africa/Cairo.

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
clinical-event deletion, guardian-consent model, encounter table or source-verified rule data exists yet.
