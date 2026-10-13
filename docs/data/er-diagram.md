# Implemented registry relationships

```mermaid
erDiagram
  PATIENTS ||--o{ PATIENT_CONTACTS : has
  CONTACTS ||--o{ PATIENT_CONTACTS : links
  PATIENTS ||--o{ PATIENT_ALIASES : has
  PATIENTS ||--o{ ALLERGIES : reviews
  PATIENTS ||--o{ FORM_RESPONSES : has
  PATIENTS ||--o{ ENCOUNTERS : visits
  ENCOUNTERS ||--o{ ENCOUNTER_ADDENDA : corrections
  PATIENTS ||--o{ DOCUMENTS : attachments
  ENCOUNTERS o|--o{ DOCUMENTS : optional_visit
  DOCUMENTS ||--o{ DOCUMENT_SCANS : evidence
  PATIENTS ||--o{ INVESTIGATION_ORDERS : requests
  ENCOUNTERS ||--o{ INVESTIGATION_ORDERS : visit
  PATIENTS ||--o{ INVESTIGATION_RESULTS : reports
  INVESTIGATION_ORDERS o|--o{ INVESTIGATION_RESULTS : optional_request
  DOCUMENTS o|--o{ INVESTIGATION_RESULTS : source
  INVESTIGATION_RESULTS o|--o| INVESTIGATION_RESULTS : correction
  FORM_DEFINITIONS ||--o{ FORM_RESPONSES : exact_version
  PATIENTS ||--o{ IDEMPOTENCY_KEYS : created_by_request
  PATIENTS ||--o{ AUDIT_EVENTS : optional_record_reference
```

Patient/contact/alias/allergy/response/idempotency foreign keys include clinic scope.
Audit record references are logical and may be absent for search/access events. The audit table is
clinic-scoped; snapshots preserve changes even when an editable profile is replaced.
Encounters contain structured note/raw observation JSON and historical birth context; audit preserves
draft replacements. Other clinical modules from the baseline remain planned.
