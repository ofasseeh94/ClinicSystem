# Milestone ledger

| Milestone | Status | Scope and limitations |
| --- | --- | --- |
| M0 | TESTED locally | Structure, dependency installation on NTFS, typecheck/build, lint and PostgreSQL runtime checks. Docker startup remains untested on this workstation. |
| M1 / Unit 01 | TESTED for synthetic development | Registry, guardian contacts, aliases, explicit allergy review, search, duplicate review, revision/audit, form v1/v2, overview. Live managed login/MFA, guardian sharing/authority administration, form publishing UI and production gates remain open. |
| M2 / Unit 02 | TESTED for synthetic development | Dated encounters, draft/review/sign/cancel lifecycle, immutable signed snapshots/addenda, raw measurements, saved birth context/age and timeline. Clinical algorithms and production gates remain pending. |
| M3 / Unit 03 | TESTED for synthetic development | Encrypted bounded attachments, authenticated ticketed retrieval, withdrawal/scanner lifecycle, investigation orders/results/corrections. ClamAV protocol fixtures tested; real scanner deployment and production storage/restore gates pending. |
| M4 / Unit 04A | PARTIAL: foundation tested for synthetic development | Catalog identity/source/version workflow and reported medication history/corrections. No approved dose/interaction knowledge, calculator or prescription lifecycle; reference selection and independent clinical validation still required. |
| M5–M10 | PLANNED | Growth/vaccines/development, tasks, AI and parent access. |

TESTED refers to the executable development acceptance suite. No unit is CLINICALLY_VALIDATED
or PRODUCTION_READY. Remote Actions results are recorded separately in the validation report.
