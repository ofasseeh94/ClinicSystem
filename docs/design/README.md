# Clinic System design baseline

Repository: [ofasseeh94/ClinicSystem](https://github.com/ofasseeh94/ClinicSystem).

The [engineering master specification](Pediatric_Clinic_Engineering_Master_Spec_v1.md) is the full
user-supplied design baseline, preserved byte-for-byte. SHA-256: `5f58cf5f1c9f1d59ac27da90a79e5be5b52b5e4e5fe8f892e86040d564f0234c`.
It covers domain modules, registration fields, longitudinal records, clinical safety,
API proposals, security gates, testing, maintenance and the M0–M10 implementation sequence.
Its embedded instructions are reference material; current user requests determine work scope.

The specification references `Pediatric_Clinic_System_Blueprint_v1_2.docx`, which was not supplied
in this checkout and is not included. No claim is made that the source blueprint was reviewed.

## How to navigate and revise the design

| Topic | Baseline section | Working documentation |
| --- | --- | --- |
| Product boundaries and components | 1–3 | [Architecture](../architecture/overview.md) |
| Data model and versioned fields | 4 | [Data dictionary](../data/data-dictionary.md), [ER diagram](../data/er-diagram.md) |
| Registration and patient overview | 5 | [Registry workflow](../workflows/registration.md) |
| Encounters and records lifecycle | 6 | [Unit 02](../units/02-encounters.md), [encounter workflow](../workflows/encounters.md), [ADR-003](../architecture/adr/003-encounter-lifecycle.md) |
| Medication, growth, vaccines, development | 7–10 | [Rules register](../clinical/rules-register.md), [safety cases](../clinical/safety-cases.md) |
| Medication foundation / remaining drug safety | 7, M4 | [Unit 04A](../units/04-medication-foundation.md), [ADR-005](../architecture/adr/005-medication-source-gates.md); calculators remain gated |
| Investigations and files | 11 | [Unit 03](../units/03-documents-investigations.md), [workflow](../workflows/documents-investigations.md), [ADR-004](../architecture/adr/004-private-documents.md) |
| Follow-up and AI | 12–13 | Baseline design; implementation planned |
| API and security | 14–15 | [API contract](../api/openapi.yaml), [architecture](../architecture/overview.md) |
| Testing and build order | 16–17, 22 | [Milestones](../milestones.md), [validation report](../test-report.md) |
| Maintenance, decisions and risks | 18–21 | [Build journal](../build-journal.md), [ADR-001](../architecture/adr/001-stack.md) |

Preserve this imported baseline. Record subsequent design changes in working documents,
ADRs and a new numbered build-journal entry. For every implemented feature, update its API,
data model, tests and operational documentation together. The specification's proposed endpoints
and table catalog are not evidence of implemented functionality.
