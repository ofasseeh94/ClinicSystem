# Unit 02 — encounters and dated measurements

Entry point: open a patient, then **Encounters**. Start a dated visit with its reason and
consent context; enter history, examination, assessment and plan; record allergy/medication
review and optional dated measurements. Save the draft with a reason, submit for review,
then sign with a reason. Return a review to draft to revise it. Cancel an unsigned visit
with a reason. Signed visits accept separately signed addenda, never replacements.

## How it was built

1. Added migration 003 alongside the existing registry migrations; historical migrations are unchanged.
2. Added strictly validated encounter/note/measurement/status/addendum request and response schemas.
3. Built clinic-scoped SQL and transactional services using the existing audit chain. Each draft
   replacement and status change captures before/after snapshots, actor, time and reason.
4. Added role-controlled routes, mandatory If-Match for changes, and UUID retry keys for creates/addenda.
5. Added the responsive timeline/editor inside the patient overview and generated API contracts.
6. Exercised real PostgreSQL lifecycle, concurrency, permissions, immutable triggers and browser flows.

## Storage and preservation decisions

`encounters` holds the current note and up to 50 dated measurements as JSON, with a monotonically
increasing encounter version. Draft revisions live in the existing immutable audit snapshots;
there is no separate note-version table or clinical condition/order table in this increment.
Signing freezes the entire encounter row, including note, measurement metadata and birth context.
`encounter_addenda` stores independently attributed, immutable corrections and signing timestamps.
Addenda do not advance the parent's version; multiple valid corrections can append concurrently.
Requests return addenda ordered by signing time and ID.

Birth context snapshots the DOB, precision, source and patient version at visit creation. Age in
days uses the Cairo calendar date, not today's age. Uncertain DOB suppresses exact age.
Measurement age is rendered from its date and that saved context; no corrected age or percentile
is calculated. Later DOB corrections leave old context intact; explain historical errors through
an addendum. Visit date and identity are immutable; cancel an incorrect unsigned visit and create
a replacement. A signed date error needs an explanatory addendum.

Measurements record kg/cm explicitly, date/time, position, technique, equipment and source.
Positive finite values are required; broad upper input bounds are technical protections, not
clinically approved plausibility thresholds. Omitted numbers remain missing, never zero.
Draft replacement/removal preserves the previous values in audit evidence. Correct a signed
measurement through an addendum; a structured measurement-correction workflow is deferred.

Registrar may read encounters; clinician/admin may read/write/review/sign/cancel/append.
Actor comes from authentication; the client cannot impersonate a provider or supply signing time.
Signing requires all four narrative sections and both review acknowledgments. It does not clear
unknown allergies or create medication orders. Consent text records context without granting authority.
This is staff attestation, not a cryptographic document signature; live OIDC/MFA remain pending.

## Editing and failure recovery

The timeline is paginated, 20 visits per page. Open a visit to reload it from the server.
If-Match rejects stale saves/status changes with 412. Unsaved fields stay visible; reload deliberately
to review the newer snapshot. Save before switching tabs; leaving through the main registry button
or reloading the page warns about unsaved entries. Closing/expiring a session still clears local state.
Drafts are saved explicitly; no browser persistence or automatic background save exists.

Creation UUIDs preserve the exact original creation response after later edits. Repeating the same
UUID/data/actor is safe; different data returns 409. Addendum UUIDs prevent duplicate corrections;
replay returns the current signed parent with its addenda. Draft/status retries with an old ETag
return 412; reload to determine whether the first save succeeded. API timestamps are normalized
to UTC; input fields use device local time, while timeline/signing display uses Cairo.

Migration 003 is additive and preserves registry data. Apply it through `scripts/migrate.py` or
the development launcher; readiness now requires three migrations. Never edit an applied migration.
Rollback is not destructive: stop writes and restore an independently verified backup if required.
Backup restore has not been tested; real data remains outside this development scope.

## Complete change manifest and modification map

| File | Purpose / where to change behavior |
| --- | --- |
| `db/migrations/003_encounters.sql` | Tables, scoped FKs, status/version rules and immutable triggers; extend through a new migration. |
| `services/api/src/clinic_api/encounters/__init__.py` | Domain package boundary. |
| `services/api/src/clinic_api/encounters/schemas.py` | Request/response validation, measurement units/bounds, note fields. |
| `services/api/src/clinic_api/encounters/service.py` | Transactions, birth snapshot, replay, transitions, completeness and audit. |
| `services/api/src/clinic_api/encounters/routes.py` | Endpoints, pagination, authorization/read audit and ETags. |
| `services/api/src/clinic_api/auth.py` | Encounter role permissions. |
| `services/api/src/clinic_api/main.py` | Router registration and migration readiness. |
| `packages/shared-contracts/encounters.ts` | Frontend response types; keep aligned with schema changes. |
| `packages/shared-contracts/openapi.json`, `docs/api/openapi.yaml` | Generated contracts; regenerate with `scripts/export-openapi.py`. |
| `apps/web/src/Encounters.tsx` | Timeline, entry fields, review/sign/addendum controls, retry keys and unsaved safeguards. |
| `apps/web/src/PatientOverview.tsx` | Encounter tab, local navigation guard and activity guidance. |
| `apps/web/src/App.tsx` | Registry navigation guard and updated module navigation text. |
| `apps/web/src/style.css` | Responsive timeline/editor/measurement styles. |
| `tests/integration/test_encounters.py` | PostgreSQL lifecycle, isolation, permissions, concurrency, dates, finite values and immutability. |
| `tests/e2e/encounters.spec.ts` | Executable staff browser workflow and desktop/mobile screenshots. |
| `docs/screenshots/unit-02-encounter.png`, `docs/screenshots/unit-02-mobile.png` | Fictional UI evidence. |
| `README.md`, `docs/00-index.md` | Entry points and links. |
| `docs/architecture/overview.md`, `docs/architecture/adr/003-encounter-lifecycle.md` | Current boundaries and preservation rationale. |
| `docs/data/data-dictionary.md`, `docs/data/er-diagram.md` | Added storage and relationships. |
| `docs/workflows/encounters.md` | Staff workflow. |
| `docs/milestones.md`, `docs/test-report.md`, `docs/change-log.md`, `docs/screenshots/README.md` | Status and actual validation evidence. |
| `docs/build-journal.md`, `docs/units/02-encounters.md` | Step 007 and this modification guide. |

Existing dependency versions and CI commands are reused. No prescription, investigation, document,
growth reference, vaccination, AI or parent feature is implemented here. Clinical review, consent/
authority administration, production identity/security and operational release gates remain open.
