Developer navigation map, data contracts, implementation sequence, security controls, and lifecycle documentation

Document ID PCS-ENG-001  |  Baseline: Pediatric Clinic System Blueprint v1.2  |  Status: Proposed technical specification; not a declaration of deployed functionality

Audience: product owner, Codex development agent, software engineer, clinician reviewer, security reviewer, and any future maintainer.

# Document control and interpretation

| Item | Definition |
| --- | --- |
| Owner | Clinic product owner / clinical lead |
| Baseline source | Pediatric_Clinic_System_Blueprint_v1_2.docx; Option C confirmed |
| Technical choices | Proposed defaults. Must be recorded as ADRs if changed. |
| Prototype status | Prior blueprint describes a local browser demonstration; source code availability and functionality must be independently verified. |
| Clinical deployment gate | Do not enter real patient information until privacy, security, backup, clinical validation and authorization sign-offs are complete. |
| Change policy | Update the code, tests, migrations, API contract and relevant documentation in the same change. |

# 1. Scope, product goals and boundaries

Build a private pediatric electronic medical record with configurable quick/expanded registration; searchable longitudinal records; encounter notes; medication ordering; investigations and documents; growth, vaccination and developmental surveillance; physician follow-up tasks; eventual parent messaging and carefully controlled AI assistance.

# 1.1 Confirmed requirements

- Option C registration: minimal fast registration plus optional expanded medical background and configurable additional fields.
- Unique patient identity and retrieval by code, Arabic/English names, guardian and telephone; maintain historical visits, treatments and uploads.
- Pediatric doses derived from verified indication-, age-, weight- and formulation-aware rules with maxima and safety checks.
- Egyptian compulsory and additional vaccination tracking, due/overdue/catch-up based on verified records.
- Sex- and age-specific growth reference plotting across visits and appropriate milestone/developmental assessment.
- Physician-entered reminders and eventual consent-based parent reminders and engagement.
- Data model must evolve without erasing existing history; clinician remains final decision-maker.

# 1.2 Non-goals for first production release

- Autonomous diagnosis, autonomous prescribing, unsupervised release of AI interpretation, and silent chart changes.
- Parent-facing application and outbound messages until separate consent, secure delivery and notification safeguards are built.
- Clinical rules inferred from generic LLM responses or unverified web content.

# 1.3 Implementation assumptions requiring confirmation

| Decision | Proposed baseline | Change procedure |
| --- | --- | --- |
| Platform | Responsive web client + protected backend API | ADR + integration impact review |
| Database | PostgreSQL with relational core and JSONB only where suitable | Migration and query strategy review |
| Object storage | Private encrypted bucket, signed short-lived downloads | Security review |
| Backend | Python FastAPI or TypeScript NestJS (select ONE before coding) | Record chosen stack in ADR-001 |
| Frontend | React + TypeScript | ADR-002 if changed |
| Authentication | Managed identity provider, MFA for clinicians | Threat-model update |
| Deployment | Initially single-clinic, multi-user-capable design | Data tenancy and permissions review |
| Language | Arabic/English capture and search; bilingual parent content later | Localization testing |

# 2. System context and component boundaries

```text
Clinician browser → Auth gateway → Application API → PostgreSQL
                                             ↘ Private document storage
                                             ↘ Clinical reference / rules service
                                             ↘ Async tasks / notification queue (later)
                                             ↘ AI gateway (later, limited/de-identified by policy)
Audit events receive write events from all relevant state changes.
```

The client never directly accesses database credentials, object-storage secrets, medication rule internals or LLM provider credentials. The backend is the only enforcement point for authorization, clinical rule invocation and durable writes.

# 2.1 Domain modules and ownership

| Module / owner | Owns | Does NOT own |
| --- | --- | --- |
| Identity & Registry | patients, identifiers, guardians, contact authority, duplicate review | encounters, clinical decision rules |
| Clinical record | encounters, note versions, conditions, allergies, medication statements | prescribing reference definitions |
| Measurements & growth | measurements, source/calc metadata, trajectories | raw identity changes |
| Medication ordering | orders, formulations, safety review result | freeform model dosage decisions |
| Investigations | orders, samples/results, attachments | file blob persistence internals |
| Immunization | administration events, evidence, schedule evaluation | editing national schedule without approval |
| Development | age checklists, observations, screening instruments | autonomous diagnosis |
| Follow-up | internal tasks, assignments, status | sending clinical details without consent |
| AI gateway | approved context retrieval, suggestions, prompt/model audit | source of truth, unsigned clinical writes |
| Knowledge management | clinical reference versions and approval | patients and consent |

# 3. Repository navigation map: required structure

```text
pediatric-clinic/
  README.md                    # setup, local demo, known limitations
  docs/
    00-index.md                # maintained navigation hub
    architecture/overview.md  # context, diagrams, security boundaries
    architecture/adr/         # immutable decision records
    data/data-dictionary.md   # tables, fields, enums, provenance
    data/er-diagram.md        # relationship graph
    api/openapi.yaml          # published API contract
    clinical/rules-register.md# approved rules + source/version
    clinical/safety-cases.md  # hazards, mitigations, tests
    workflows/                # UI flow, role transitions
    operations/runbooks/      # backup, restore, incidents, deploy
    change-log.md             # human-readable migrations / changes
  apps/web/                   # clinician-facing interface
  services/api/              # API, authz, business logic
  packages/shared-contracts/ # validated types / enums
  packages/clinical-rules/   # deterministic rule interfaces
  db/migrations/             # ordered irreversible history
  db/seeds/                  # synthetic test data only
  tests/unit/ integration/ e2e/ security/ clinical/
  scripts/                    # one-shot setup/check commands
  infrastructure/             # declarative deployment, secrets refs only
  .env.example                # placeholders; NEVER real secrets
```

Code ownership guideline: each domain has routes/controllers, service logic, repository/query layer, types, validation, and tests. Avoid a single oversized application file. Every documented path must correspond to a real file once implemented.

# 4. Data model: permanent core and extensibility

Use a normalized longitudinal relational core. Every row carries stable ID, creation/update timestamps, attribution and organization/clinic scope where appropriate. Hard deletion of clinical events is normally prohibited; prefer amendment, cancellation or archived state.

# 4.1 Core entity catalog

| Entity | Important fields | Cardinality / lifecycle |
| --- | --- | --- |
| patients | id UUID; clinic_code UNIQUE; names AR/EN; date_of_birth; dob_precision; growth_reference_sex; status; created_at | 1 patient → many encounters; name/sex changes audited |
| patient_aliases | id; patient_id; alias; normalized_alias; source | many aliases per patient |
| contacts | id; names; e164_phone; preferred_language; verified_at | one guardian may have many patient links |
| patient_contacts | patient_id; contact_id; relation; authority_status; emergency_priority | many-to-many; authority explicit |
| consents | id; patient_id; contact_id; channel; purpose; status; evidence; timestamps | purpose-specific versioned grants |
| allergy_reviews | id; patient_id; review_status; reviewed_by; reviewed_at | unknown vs no-known vs known; time-stamped |
| allergies | id; patient_id; substance; reaction; severity; state; provenance | many; do not use blank = none |
| conditions | id; patient_id; coded_concept; label; onset; status; provenance | longitudinal problem list |
| medication_statements | id; patient_id; drug; dose/route/frequency; source; state | reported meds distinct from orders |
| encounters | id; patient_id; date_time; provider; status; reason; signed_at | one patient → many encounters |
| notes | id; encounter_id; version; author; content; status; signed_at | signed version immutable; addendum linked |
| measurements | id; encounter_id; measured_at; weight_kg; length_cm; head_cm; technique; source | many measurements per encounter |
| growth_calculations | id; measurement_id; reference_id; age_basis; z_score; percentile; flags | derived snapshots, recomputable |
| prescriptions | id; encounter_id; medication_catalog_version; indication; instructions; status; signed_by | orders distinct from historical meds |
| dose_checks | id; prescription_id; rule_version; inputs_snapshot; result; alerts; review | immutable evidence of calculation |
| investigation_orders | id; encounter_id; test_code; urgency; ordered_at; status | orders track separately from results |
| investigation_results | id; order_id nullable; collected_at; observed_at; unit; interpretation; attachment_id | unlinked external results allowed |
| documents | id; patient_id; encounter_id nullable; category; object_key; hash; status | metadata only; blobs in private store |
| immunizations | id; patient_id; antigen/product; dose_no; date; evidence; administered_elsewhere | historical actual event only |
| vaccine_assessments | id; patient_id; schedule_version; date; input_snapshot; due_status | derived, source traceable |
| development_observations | id; patient_id; encounter_id; milestone_id; status; date; reporter | observed ≠ screened ≠ diagnosed |
| screening_results | id; patient_id; instrument/version; age; score; reviewer; date | validated tool and interpretation |
| tasks | id; patient_id; encounter_id nullable; owner; reason; due_at; priority; status | internal follow-up queue |
| notification_events | id; patient_id; consent_id; template_version; channel; delivery_state | later, audit sends and failures |
| field_definitions | id; stable_key; domain; data_type; validation; status | versioned registry of optional fields |
| form_definitions | id; key; version; published_at; schema_snapshot | published versions immutable |
| form_responses | id; patient_id; encounter_id; form_version_id; answers; author; date | preserve old responses |
| audit_events | id; actor; action; entity; record_id; before_hash/after_hash; reason; time | append-only privileged audit trail |

# 4.2 Field modeling and unknown states

Every clinically significant answer must distinguish NOT_RECORDED, UNKNOWN, NOT_ASSESSED, NOT_APPLICABLE, NEGATIVE, POSITIVE, and DECLINED where meaningful. Avoid a universal Boolean that collapses unknown into false. Standardize units and typed dates rather than storing ambiguous free-text amounts.

# 4.3 Configurable field metadata

| Property | Example | Rule |
| --- | --- | --- |
| field_key | birth.nic_admission | Immutable stable namespace; no meaning changes |
| label_ar / label_en | رعاية مركزة / NICU admission | Labels can change without altering key |
| type | enum: yes,no,unknown | Type changes via new version + transform plan |
| scope | patient_profile / encounter / procedure | Do not cross scope silently |
| required_when | form=neonatal AND prematurity=yes | Conditional client + server validation |
| terminology | local code + optional SNOMED/LOINC mapping | Mappings versioned, license checked |
| privacy_class | clinical_sensitive | Access controlled |
| effective dates | published_at / retired_at | Old versions remain readable |
| source | clinician / guardian / imported / AI_suggested | AI suggestions never presented as verified |
| display_order | section=Birth history, order=4 | Schema drives form rendering |

# 4.4 Schema change rules

1. Propose field: define clinical meaning, intended scope, owner, allowed values, units and privacy classification.
2. Create new version: publish immutable form revision; preserve previous forms and submissions.
3. Plan migration: only modify normalized tables when a true new invariant/relationship is required; write reversible or recovery-backed migration.
4. Backfill selectively: distinguish observed historical data from computed/inferred data; never manufacture missing values.
5. Update UI and API validation simultaneously; preserve older client compatibility when necessary.
6. Add tests for old and new data, export, restore, permissions, and derived rule changes.
7. Record change log + ADR when domain meaning or architecture changes.

# 5. Registration (Option C): complete field contract

| Section | Field | Required / behavior |
| --- | --- | --- |
| System identity | patient_id, clinic_code, created_by, timestamps | Generated server-side; unique and immutable |
| Demographic | name_ar or name_en | At least one name; preserve accents/original |
| Demographic | DOB, DOB precision/source | Exact default in prototype; uncertain DOB must be expressible in production |
| Demographic | sex used for growth-reference selection | Recorded/unknown; prevent chart calc when insufficient |
| Contact | guardian full name + phone | Quick registration; identity/authority separate verification |
| Contact | relation, verification, emergency contact | Expandable profile; permissions not inferred |
| Safety | allergy review status, substance/reaction | Expandable; unknown allowed and visible |
| Medical | chronic conditions, prior admissions, medications | Expandable and date/source stamped |
| Birth/neonatal | GA weeks+days; birth weight; NICU; ventilation; intubation | Expandable and conditional; unknown permitted |
| Respiratory | wheeze, croup, stridor, asthma, smoke exposure | Optional versioned specialty questionnaire |
| Social | nursery, household factors, parent preferences | Avoid irrelevant mandatory collection |
| Communication | language, communication opt-in, consent evidence | Separate clinical necessity from marketing consent |
| Custom | field-definition driven additions | Allowed only with controlled field publishing |

# 5.1 Registration and search workflow

1. Search before create by exact clinic code, normalized Arabic/English partial name, aliases, verified phone and guardian name.
2. Display masked duplicate candidates with date of birth and relevant context; deliberate selection, no automatic merging.
3. Quick-create patient and guardian link in one transaction; reject duplicate clinic codes and invalid data.
4. Offer expandable sections (allergies, neonatal, chronic history, medication statements, configurable fields).
5. Show complete summary with unreviewed flags; save changes with actor and timestamp.
6. Open patient overview; tabs have meaningful empty states and recent-record access.
7. Allow corrections only with audit reason, previous value and recomputation flag for dependent values.

# 5.2 Patient overview navigation

```text
Header: Name | clinic code | DOB/age at visit | allergy banner | recent measurements/date
Tabs: Overview | Encounters | Growth | Vaccines | Development | Medications | Investigations | Documents | Tasks
Overview: left background/history; center visits, meds; right clinical tasks and pending tests
Every widget: data source + effective date + verified state + access/permission boundary
```

# 6. Encounter workflow and records lifecycle

Encounter statuses: DRAFT → IN_REVIEW → SIGNED; optional CANCELLED with reason. SIGNED entries must be immutable; mistakes corrected by signed ADDENDUM with attribution. Concurrent edits use optimistic locking/version counters.

| Stage | Inputs | Outputs |
| --- | --- | --- |
| Start visit | patient ID, clinician, date/time, consent context | draft encounter; time-correct age |
| History | complaint, HPI, pertinent negatives, medication and allergy review | structured note + editable narrative |
| Examination | vitals, anthropometrics, systems examination | time-stamped observations |
| Assessment | diagnosis code/text, problem status, clinical reasoning | assessment list |
| Plan | medications, investigations, counseling, follow-up | draft orders and tasks |
| Sign | review completeness, errors, clinical alerts | immutable signed snapshot and audit event |
| Reopen | read-only signed note + linked addenda | full historical context |

# 7. Medication knowledge and dosage rule engine

Clinician-curated dosage knowledge base with reviewed, licensed sources. Separate catalog drug, ingredient, formulation and strength; dose rule by indication/age/weight/route, renal/hepatic context where appropriate; maximum per dose/day and contraindication/interactions. Never use an LLM as dosage source.

```text
input: patient_age, measured_weight+date, drug_id, indication, strength, route, interval, allergies, co-medications
→ verify data freshness/precision + rule applicability
→ compute dose and formulation-specific volume/units using decimal arithmetic
→ cap/check max dose and cumulative exposure; check age restrictions and interactions
→ show math + provenance + warnings → physician review/signature
→ persist input snapshot, rule version, calculation and override reason
```

- Weight missing/stale, uncertain age, absent indication, ambiguous concentration, unknown allergy history, unavailable interaction knowledge or renal concerns: produce an explicit blocking/needs-review state rather than false reassurance.
- Allergy conflicts or serious contraindications need severity-based alerting; no unsupported “safe” label if a drug-interaction dataset is absent.
- Dose rules require independent pediatric pharmacist/clinical verification, regression fixtures and documented periodic review.

# 8. Growth engine

Record measurements with date/time, units, technique, equipment and recumbent vs standing status. Derive age at measurement (corrected age if relevant) and reference selection. Persist WHO or other formally approved reference ID/version and percentile/z-score output with uncertainty flags.

- Use WHO Child Growth Standards for early childhood and age-appropriate older-child references; verify exact reference ranges and implementation against the published data.
- Chart raw points at each visit and reference centile curves; do not join data from incompatible measures or silently interchange length and height.
- Flag implausible measurements, crossing centiles and potential faltering trends for review, not autonomous diagnosis.
- Regression tests against trusted reference examples are mandatory before enabling for real patients.

# 9. Immunization engine

Store what was actually administered separately from scheduled/recommended doses. Verified dates and source evidence are mandatory for marking complete. Maintain effective-dated, approved Egypt compulsory schedules and separate additional vaccine knowledge, product/antigen composition and catch-up logic.

- Statuses: VERIFIED_COMPLETE, REPORTED_UNVERIFIED, DUE, OVERDUE, CATCH_UP_REVIEW, FUTURE, DEFERRED, CONTRAINDICATED, UNKNOWN.
- Do not equate a due vaccine with vaccination. Handle series intervals, contraindications, prior records, and uncertain histories via clinician review.
- Store schedule/version/input snapshot for historical assessments; updated schedules may require reassessment and explanation.
- Local schedules, formulations and recommendations need current Egyptian clinical verification before activation.

# 10. Developmental surveillance

Age-based milestone library with category (gross/fine motor, language/receptive, cognition, social-emotional, sensory surveillance), observation/evidence status and next assessment window. Keep surveillance separate from validated formal screening instrument results.

- Observation statuses: achieved, not yet, uncertain, not assessed, skill lost/regression. Preserve reporter and observation date.
- Do not diagnose from checklist alone; escalation pathways present clinician actions and validated screening options.
- Reference checklist edition/version and instrument scoring rules. Do not change historical observations when guideline updates occur.

# 11. Investigations, attachments and longitudinal retrieval

Orders have clinical indication, priority, encounter link, requested-by and status. Results may be manually entered or linked to external order; attach source PDF/image and distinguish structured values from AI-extracted text. Files need MIME validation, malware scanning, content hash, restricted access and upload lifecycle.

```text
private object store: /tenant/<opaque-id>/patient/<uuid>/doc/<uuid> (illustration only)
metadata DB: document_id, patient_id, encounter_id, category, captured_at, uploaded_by, source, SHA256, storage_key, status
retrieve: authorized short-lived signed download only; never public permanent URLs
```

# 12. Tasks, follow-up, notifications and parent access

Internal follow-ups: user-created or AI-drafted task requires clinician confirmation; due dates, priority, owner and status. Parent communications require guardian authority, separate opt-in where relevant, safe content templates, delivery tracking, opt-out and contact verification.

- Notification content should minimize clinical details on lock screens or shared phones.
- No automated celebration of unconfirmed milestones, and no suggestion that a missed vaccine was administered.
- Escalation tasks for potentially urgent issues must have human ownership and failure/retry reporting.

# 13. AI integration and safety contract

AI is optional, access-limited and isolated behind an AI Gateway. Allowed tasks: draft notes, summarize chart excerpts, identify missing history questions, prepare physician-reviewed letters and parent language. It cannot authorize meds, mark vaccines complete, amend signed charts or change follow-up actions without confirmation.

| Control | Implementation contract |
| --- | --- |
| Context | Only minimum permitted patient facts, selected by authorized clinician; scoped to current patient/encounter |
| Output | Typed JSON for suggestions, with citations to chart source IDs and uncertainty status |
| Source traceability | Source records and timestamps listed; no hidden patient facts |
| Human decision | Suggestions saved to draft area; explicit accept/edit/reject before record modification |
| Logging | Model/version, prompt template version, input references, output metadata, actor and decision |
| Privacy | Provider contract/retention/training review and safeguards before identifiable use |
| Failure | AI timeout/unavailable never prevents core documentation or patient retrieval |

# 14. API and contracts (initial proposed endpoints)

| Operation | Route | Permission / behavior |
| --- | --- | --- |
| Search | GET /v1/patients?query= | AUTHORIZED_CHART_READ; paginated; masked results |
| Create | POST /v1/patients | REGISTRY_CREATE; idempotency key; transaction |
| Profile | GET /v1/patients/{id} | PATIENT_READ; includes ETag/version |
| Update | PATCH /v1/patients/{id} | PATIENT_EDIT; optimistic lock + audit reason |
| Contacts | POST /v1/patients/{id}/contacts | GUARDIAN_EDIT; verify access separate |
| Allergies | GET/POST /v1/patients/{id}/allergies | CLINICAL_READ/EDIT; explicit review state |
| Form schema | GET /v1/forms/{key}/versions/{version} | SCHEMA_READ; immutable published definition |
| Form answer | POST /v1/patients/{id}/form-responses | CLINICAL_EDIT; version validated |
| Overview | GET /v1/patients/{id}/overview | aggregated read with data provenance |
| Encounter | POST /v1/patients/{id}/encounters | ENCOUNTER_CREATE; initially deferred |
| Audit | GET /v1/audit?entity_id= | PRIVILEGED_AUDIT_READ; read-only |

All APIs: JSON schema validation; predictable problem+json errors; server timestamps in UTC and clinic-local rendering; pagination; trace/request ID; rate limits; no secrets/PHI in URLs, analytics or error logs. Add/update OpenAPI with every endpoint change.

# 14.1 Example request and response envelopes

```text
POST /v1/patients
{ "name_ar":"طفل تجريبي", "dob":"2024-06-01", "dob_precision":"exact",
  "growth_reference_sex":"female",
  "guardian": {"name":"ولي أمر تجريبي", "phone_e164":"+201000000000"} }

201 Created
{ "patient_id":"<server-generated-uuid>", "clinic_code":"PC-000123",
  "status":"active", "version":1, "warnings":[] }

409 duplicate_candidate: show candidates, require deliberate resolution; NEVER auto-merge
```

# 15. Security, privacy, reliability and clinical deployment gates

| Category | Minimum gate |
| --- | --- |
| Identity | Unique staff accounts, MFA, least privilege and session timeout |
| Authorization | Server-side role + relationship + clinic scoping; no IDOR |
| Data | Encryption in transit and at rest; key lifecycle; secret management |
| Audit | Tamper-evident append-only access/change logs; privileged access reports |
| Documents | Private storage, signed access, upload scanning, backups |
| Availability | Backup schedule, restore drills, tested outage/recovery procedure |
| Privacy | Legal review of Egyptian data protection/healthcare obligations and vendor transfers |
| Clinical rules | Clinical sign-off, reference licensing, independent dose/catch-up/chart test suite |
| AI | Provider data-processing/retention assessment, human-in-the-loop safeguards |
| Release | Synthetic data in development, staging verification, sign-off before real PHI |

# 16. Testing strategy and example acceptance criteria

| Test class | Required scenarios |
| --- | --- |
| Unit | Arabic normalization, DOB age calculation, guardian phone validation, custom field type checking |
| Integration | atomic register/link contacts, duplicate candidate query, authorized chart loading, migration compatibility |
| E2E | search → create → expanded form → save → reopen → edit with audit |
| Data lifecycle | old form v1 responses survive v2 publication; signed note only amendable |
| Clinical | boundary weights, max doses, unknown allergy, stale anthropometrics, known-reference growth values |
| Security | unauthorized cross-chart access denied, file access expiration, log redaction |
| Resilience | DB restoration, storage failure, AI unavailable, duplicate request idempotency |
| Accessibility/localization | Arabic RTL search/display; keyboard navigation; error and empty states |

# 17. Build order and precise deliverables

| Milestone | Implement | Definition of done |
| --- | --- | --- |
| M0 / repository | mono-repo skeleton; ADR-001 tech choice; lint/test/CI; docs index | clean clone/install/test, no secrets |
| M1 / registry | patients/guardian links/search/registration; custom field schemas; audit | fictional E2E test + SQLite prohibited as production source of truth |
| M2 / encounters | notes, signatures/addenda, timeline, dated measurements | signed note immutable; age-correct history |
| M3 / documents | orders/results, secure uploads/viewer | permission checks, hash, retrieval, scan |
| M4 / drug safety | verified catalog, dose calculator, max warnings | independent clinical validation passed |
| M5 / growth | reference import and sex-specific chart rendering | trusted WHO fixture agreement |
| M6 / immunization | Egypt schedule versions and verified event tracking | catch-up/overdue clinical acceptance |
| M7 / development | age-based surveillance and screening workflows | age-window test suite |
| M8 / follow-up | clinician reminders; work queue | no notification without authorized review |
| M9 / AI | limited chart summary and note drafts | no autonomous writes; full provenance |
| M10 / parents | secure portal, verified guardian, consent-based notifications | privacy/security review, opt-out, monitoring |

# 18. Maintenance playbook: how a future developer changes the system

# 18.1 Before any change

1. Read README.md and docs/00-index.md, then current architecture and change log.
2. Identify owning domain, impacted tables/API/UI/rules/permissions, and existing tests.
3. Determine whether this is a new optional field, clinical semantics change, migration, new feature or defect.
4. For architectural choices, file ADR in Proposed state, including alternatives and reversal strategy.
5. Create work item with acceptance criteria, safety/privacy impact, migration/rollback and documentation target.

# 18.2 Required change packet / pull request

| File / artifact | What must change |
| --- | --- |
| Code | small isolated domain change, no unrelated rewrites |
| Schema | migration + tested staging rollback/recovery strategy |
| API | OpenAPI schema + version impact |
| Clinical source | rule register, provenance and sign-off if clinical logic touched |
| Tests | unit + integration + E2E + safety/security where relevant |
| Docs | data dictionary + navigation index + workflow + change log |
| Operational | deployment runbook if config/infrastructure changed |
| Reviewer | clinical owner for meaning; senior engineer for architectural impact |

# 18.3 Override / rollback contract

An override must have an authorized actor, scope, rationale, original value, replacement value, effective time, expiry when applicable, and audit event. Do not implement “override” by directly editing immutable signed encounters or deleting previous rule versions. If a migration cannot reverse without data loss, provide tested restore/recovery plan instead of claiming easy rollback.

# 18.4 Architecture Decision Record (ADR) template

```text
ADR-XXX: Title
Status: Proposed / Accepted / Superseded
Date and owner:
Context/problem:
Decision:
Alternatives considered:
Data, security, clinical and interoperability impact:
Migration/compatibility plan:
Testing and rollback/restore plan:
Supersedes / references:
```

# 19. Codex development instructions: copy into AGENTS.md

```text
Project objective: implement a safe, extensible pediatric clinic EMR.
1. Read docs/00-index.md, architecture, data dictionary and current milestone BEFORE coding.
2. Work in small, testable increments. Preserve patient data, IDs, audit history and published form versions.
3. Never store real PHI in seeds, fixtures, logs, prompts or external AI tools. Use synthetic data.
4. Never invent medication doses, contraindications, vaccine catch-up rules or growth reference values.
5. AI outputs are suggestions only; clinical writes require explicit authorized user action.
6. All write paths require server-side validation, authorization and audit.
7. For each change update migration, API schema, tests, docs and change log.
8. Report exactly which files changed, tests run, remaining risks, migration/rollback needs.
9. Do not claim features work without executable tests.
10. Stop and flag missing clinical source approval or security prerequisites.
```

# 20. Versioning, traceability and implementation status ledger

| Type | Version convention | Rule |
| --- | --- | --- |
| Document | Major.minor (1.0 → 1.1) | Edit history and owner |
| API | /v1, backward-compatible minor changes | Breaking changes → explicit new major |
| Database | Ordered migration IDs | Never rewrite applied migrations |
| Forms | Immutable published semantic version | Responses reference exact version |
| Clinical sources | Source edition/effective date/approved_by | Historical rule outputs retain snapshot |
| AI prompt/model | Template ID + model version | Every generated suggestion traceable |
| Application | Semantic release version + Git commit | Reproducible deploy |

Implementation statuses for every feature: PLANNED, SPECIFIED, IN_PROGRESS, IMPLEMENTED, TESTED, CLINICALLY_VALIDATED, PRODUCTION_READY, DEFERRED. “Described in blueprint” does not imply implemented.

# 21. Open decisions and risk register

| ID | Decision/risk | Resolution gate |
| --- | --- | --- |
| D-01 | Select actual backend stack and hosting region | Before M0 code |
| D-02 | Exact minimum verified guardian authority model | Before parent access |
| D-03 | Egypt vaccine reference source and licensed update process | Before M6 live |
| D-04 | Approved pediatric medication reference + interaction dataset | Before M4 clinical use |
| D-05 | Clinical reference version and chart precision for preterm age | Before M5 clinical use |
| D-06 | Clinical screening instrument availability/licensing | Before M7 clinical use |
| D-07 | PII/data-processing and local legal assessment | Before real data |
| D-08 | Retention, corrections, backups and disaster-recovery targets | Before real data |
| D-09 | Notification channels, caregiver consent and ownership | Before M10 |
| D-10 | Whether previous browser prototype code is present and tested | Before porting to M1 |

# 22. Immediate first Codex sprint

1. Create repository structure above, docs/00-index.md, README.md, AGENTS.md, architecture overview, ADR-001 and environment template.
2. Select stack in ADR-001, set up database, migrations, local development containers if appropriate, lint/test/CI commands.
3. Implement identity/registry normalized tables, uniqueness constraints, audit events and test-data factory.
4. Implement authenticated quick-create and expanded configurable registration; backend validation; search and duplicate candidates.
5. Create patient overview with empty-state tabs; verify Arabic text and accurate DOB-based age calculation.
6. Execute acceptance suite with synthetic siblings, uncertain data, aliases, and custom form v1→v2.
7. Produce test report, screenshot, schema diagram, generated OpenAPI and known-limitation log. Do not claim production readiness.

# Appendix A. Baseline traceability

This handoff extends existing Pediatric_Clinic_System_Blueprint_v1_2.docx, particularly Sections 01–12 (core modules, field dictionary, rules, UI, privacy), Section 13 (registry/initial tables), Section 15 (Option C registration). This document is more prescriptive engineering guidance; any inconsistency should be explicitly resolved through an ADR rather than silently replacing previous product requirements.

# Appendix B. Recommended documentation ownership

| Document | Maintainer |
| --- | --- |
| 00-index, architecture, ER map | Tech lead |
| data dictionary, migrations | Backend owner |
| clinical rules, reference register | Pediatric clinical owner / reviewer |
| API / OpenAPI | Backend owner |
| security + incident runbooks | Security/operations owner |
| workflows and user acceptance | Product owner |
| change log / ADRs | Every change author, reviewed by lead |
