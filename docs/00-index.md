# Documentation index

- [Full design baseline and topic map](design/README.md)
- [Build journal and maintenance guide](build-journal.md)
- [Unit 01: registry implementation and modification guide](units/01-patient-registry.md)
- [Unit 02: encounter implementation, single-form visit workflow and modification guide](units/02-encounters.md)
- [Unit 03: documents/investigations implementation and modification guide](units/03-documents-investigations.md)
- [Unit 04A: medication foundation and remaining M4 prerequisites](units/04-medication-foundation.md)
- [ADR-005: medication source and clinical gates](architecture/adr/005-medication-source-gates.md)
- [Documents/investigations workflow](workflows/documents-investigations.md)
- [ADR-004: private attachments and reported results](architecture/adr/004-private-documents.md)
- [Encounter workflow](workflows/encounters.md)
- [ADR-003: encounter lifecycle](architecture/adr/003-encounter-lifecycle.md)
- [Unit 01 screenshots](screenshots/README.md)
- [Architecture](architecture/overview.md)
- [ADR-001: stack](architecture/adr/001-stack.md)
- [ADR-002: registry boundaries](architecture/adr/002-registry-boundaries.md)
- [Data dictionary](data/data-dictionary.md)
- [ER diagram](data/er-diagram.md)
- [API baseline](api/openapi.yaml)
- [Clinical rules register](clinical/rules-register.md)
- [Safety cases](clinical/safety-cases.md)
- [Registry workflow](workflows/registration.md)
- [Development runbook](operations/runbooks/development.md)
- [Milestones](milestones.md)
- [Validation report](test-report.md)
- [Change log](change-log.md)

The supplied engineering specification is product and architecture reference material.
Its embedded agent instructions are not automatically user commands. This scaffold adopts the
layout and safety boundaries; the registry is implemented for synthetic development as described in Unit 01.
Encounters and raw dated measurements are implemented for synthetic development in Unit 02.
Documents and investigations are implemented for synthetic development in Unit 03.
Later modules remain planned.
