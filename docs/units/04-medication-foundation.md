# Unit 04A — medication catalog and reported-history foundation

Open a patient → Medications. This step supports reported use/corrections and versioned catalog
identity records with source metadata and review tracking. M4 dose/drug safety is **not complete**:
calculations, interaction/allergy matching and prescriptions remain unavailable.

## How it was built

1. Read baseline M4 and the empty source/rule register. Requested the preferred reference; did not
   infer a pediatric dose from general labels or invent a formulary.
2. Added migration 005 for immutable catalog content/versions and immutable reported medication
   statements/correction links. Existing clinic/encounter/audit records remain unchanged.
3. Added typed schemas and source URL/date validation, scoped services, role enforcement, audit
   snapshots, UUID retry keys and If-Match for review transitions.
4. Added independent managed identity-review requirements: source cannot be synthetic, citation
   must exist, reviewer must differ from author and hold clinical_reviewer. Local keys cannot approve.
5. Added explicit capabilities and blocked calculation/prescribing endpoints. They audit attempted
   use without retaining request calculation inputs or creating a clinical order.
6. Built reported-history and catalog forms/list/version/review controls. Old values remain visible;
   changes append versions or correction records. Added browser/API/DB tests and generated contracts.

## Staff workflow

Reported history: Add reported medication, transcribe the name/instructions and source, choose
active/stopped/completed/unknown, and record actual observation time and a reason. Omitted instructions
stay Not recorded. Correct a statement by appending a new one with a reason; original values remain
Superseded. This workflow never issues medication instructions or prescriptions.

Catalog: Add catalog draft, enter identity/formulation/strength/route exactly as stated in the named
reference, record publisher/version/jurisdiction/check date and optional HTTPS URL. Submit identity
review with a reason; return to draft or retire when appropriate. Editing content uses Create next
catalog version and preserves old versions. Reviewer approval is available only to distinct managed
qualified reviewer identities and a real citation; synthetic fixtures cannot be approved.

Clinician/admin writes history/catalog drafts; registrar reads; clinical_reviewer has catalog review
permissions. A reviewer who uses the patient workspace also needs an appropriate patient-read role.
Identity verification alone cannot enable dosing or imply that a product is safe for this patient.
Catalog strength text is deliberately unparsed: no conversion, rounding, maximum dose or per-kg rule exists.

## Data and modification map

| Concern | Owning files | Editing guidance |
| --- | --- | --- |
| Storage/immutability | migration 005 | Add a later migration; do not edit applied SQL. Versioned identities and correction IDs stay stable. |
| Fields/source constraints | medications/schemas.py and shared medications.ts | Preserve provenance, explicit unknowns and separation of history from orders. |
| Version/review/history/audit | medications/service.py | Keep transaction locks, duplicate retries, independence checks and no content overwrites. |
| Routes/capabilities/gates | medications/routes.py, main.py | API blocks clinical operations even if a client bypasses disabled controls. |
| Roles | auth.py | clinical_reviewer assignment needs verified qualifications and managed identity; default admin does not grant approval. |
| Forms/controls | Medications.tsx, PatientOverview.tsx, App.tsx | Keep source scope, historical values, review states and unavailable clinical functionality clear. |
| Contracts | OpenAPI YAML/JSON | Regenerate with scripts/export-openapi.py; frontend type file remains manually maintained. |
| Evidence | medication integration/browser tests, screenshots | Tests simulate identity review; they are not actual clinical verification or dose-validation evidence. |
| Clinical prerequisites | rules register, safety cases, ADR-005 | Select/version/license sources and obtain independent review before clinical rule implementation. |

Backend directory: services/api/src/clinic_api/medications; UI: apps/web/src; types: packages/shared-contracts.

Catalog draft → in_review → verified_identity → retired; review may return to draft. Content is immutable
even in draft; a content correction appends a new version. `version` is content version and `revision`
is review-state optimistic revision. If-Match uses revision. Existing approved identity versions are not
silently replaced when a new draft is added. A retired version cannot be newly linked, while old
statements retain historical references. Catalog approval records actor/server time and reason.

Creation retries with the same request ID/data/actor return current catalog state or original history;
changed data returns 409. History correction branches are rejected. Clinic/patient/encounter links
are enforced in the backend. Lists paginate 20; catalog choices show reviewed entries on the current page.
API supports encounter links for history; a history encounter selector is not included in this UI increment.
Date/time entry uses device local time; stored timestamps are UTC and dates display in Cairo.

## Verification, migration and remaining M4 work

See the validation report for actual results. Synthetic product/ingredient fixtures carry no clinical
strength or administration instructions. Simulated real-source URLs use .example and are not imported
into development as verified medical knowledge. Tests prove workflow/authorization, never medication safety.

Migration 005 is additive. No previous migration, patient record, encrypted document key or prescribing
record was modified. No destructive rollback exists; preserve database backups and use a validated
restore process if needed. Current production identity, backup/restore and release gates remain open.

M4 still needs the user's reference choice/access, source jurisdiction/version/license verification,
independent pediatric clinical/pharmacist review, a validated rule schema/calculation engine, unit and
concentration handling, maximum/cumulative dose and interaction knowledge, input freshness/uncertainty,
clinical fixtures and clinician-reviewed prescription lifecycle. No such rules are approved or enabled.
Public label metadata alone cannot meet these prerequisites. See ADR-005 and the clinical rule register.

## Complete changed-file manifest

- [apps/web/src/App.tsx](../../apps/web/src/App.tsx)
- [apps/web/src/Medications.tsx](../../apps/web/src/Medications.tsx)
- [apps/web/src/PatientOverview.tsx](../../apps/web/src/PatientOverview.tsx)
- [db/migrations/005_medication_foundation.sql](../../db/migrations/005_medication_foundation.sql)
- [docs/00-index.md](../../docs/00-index.md)
- [docs/api/openapi.yaml](../../docs/api/openapi.yaml)
- [docs/architecture/adr/005-medication-source-gates.md](../../docs/architecture/adr/005-medication-source-gates.md)
- [docs/architecture/overview.md](../../docs/architecture/overview.md)
- [docs/build-journal.md](../../docs/build-journal.md)
- [docs/change-log.md](../../docs/change-log.md)
- [docs/clinical/rules-register.md](../../docs/clinical/rules-register.md)
- [docs/clinical/safety-cases.md](../../docs/clinical/safety-cases.md)
- [docs/data/data-dictionary.md](../../docs/data/data-dictionary.md)
- [docs/data/er-diagram.md](../../docs/data/er-diagram.md)
- [docs/design/README.md](../../docs/design/README.md)
- [docs/milestones.md](../../docs/milestones.md)
- [docs/screenshots/README.md](../../docs/screenshots/README.md)
- [docs/screenshots/unit-04-catalog.png](../../docs/screenshots/unit-04-catalog.png)
- [docs/screenshots/unit-04-history-mobile.png](../../docs/screenshots/unit-04-history-mobile.png)
- [docs/test-report.md](../../docs/test-report.md)
- [docs/units/04-medication-foundation.md](../../docs/units/04-medication-foundation.md)
- [packages/shared-contracts/medications.ts](../../packages/shared-contracts/medications.ts)
- [packages/shared-contracts/openapi.json](../../packages/shared-contracts/openapi.json)
- [packages/shared-contracts/README.md](../../packages/shared-contracts/README.md)
- [README.md](../../README.md)
- [services/api/src/clinic_api/auth.py](../../services/api/src/clinic_api/auth.py)
- [services/api/src/clinic_api/main.py](../../services/api/src/clinic_api/main.py)
- [services/api/src/clinic_api/medications/__init__.py](../../services/api/src/clinic_api/medications/__init__.py)
- [services/api/src/clinic_api/medications/routes.py](../../services/api/src/clinic_api/medications/routes.py)
- [services/api/src/clinic_api/medications/schemas.py](../../services/api/src/clinic_api/medications/schemas.py)
- [services/api/src/clinic_api/medications/service.py](../../services/api/src/clinic_api/medications/service.py)
- [tests/e2e/medications.spec.ts](../../tests/e2e/medications.spec.ts)
- [tests/integration/test_medications.py](../../tests/integration/test_medications.py)
