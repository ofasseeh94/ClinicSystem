# Project guidance

Read README.md, docs/00-index.md, architecture overview, data dictionary and milestone ledger before changes.
Work in small testable increments. Preserve stable IDs, audit history and published form versions.
Use synthetic data only in development, fixtures, logs and external tools.
Never invent doses, growth references, vaccine schedules or clinical rules.
Clinical AI outputs remain suggestions and require authorized clinician acceptance.
Feature write paths require server validation, authorization and audit.
Update applicable migrations, API contracts, tests, documentation and change log together.
Report checks actually run, known limitations and migration or recovery needs.
Do not claim production readiness without clinical, privacy, security and operations sign-off.

After every build step, update docs/build-journal.md with the purpose, implementation sequence, complete file changes, design decisions, modification guide, data/migration and recovery impact, actual verification results, limitations and next prerequisites. Preserve earlier entries and reference them when superseded. Link the updated journal in the user-facing completion report. Read the journal before revisiting earlier work. Include commit/PR references when available; never invent repository URLs or validation results.
