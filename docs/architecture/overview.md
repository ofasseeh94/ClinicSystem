# Architecture

```mermaid
flowchart LR
  Browser[React registry] -->|same-origin /api| Proxy[Vite development proxy]
  Proxy --> API[FastAPI routes]
  API --> Auth[Staff identity and role permissions]
  API --> Service[Registry service and validation]
  Service --> PG[(PostgreSQL)]
  Service --> Audit[Atomic audit chain]
  Audit --> PG
```

Implemented: patient/guardian identity, aliases, allergy review, masked searches, duplicate review,
optimistic revisions, immutable versioned background responses and access/change audit evidence.
See ADR-002 for transaction, search and auth decisions.

The browser never receives database credentials. API permissions and all patient queries use the
principal's clinic ID; clients cannot choose a clinic ID in registration requests. Development uses
an explicit synthetic staff key, with loopback servers. Production configuration requires managed OIDC
and forbids development credentials. Live IdP integration and browser OIDC login remain unfinished.

Search inputs are sent in POST bodies; no analytics, external fonts or AI calls are configured.
Tokens live only in browser memory. Server errors omit supplied input values; configuration repr hides credentials.

Unit 02 adds clinic-scoped dated encounters, structured narrative notes, raw measurements,
review/signing/cancellation and immutable signed addenda. Draft revisions are preserved in audit
snapshots; signed rows are protected by PostgreSQL triggers. See ADR-003 and the Unit 02 guide.
Unit 03 adds encrypted bounded attachments, scoped short-lived download tickets, upload/scanning/
withdrawal history, investigation requests, source-attributed results and immutable corrections.
The first private storage backend is PostgreSQL ciphertext; future object storage is documented in ADR-004.
Missing malware scanning quarantines attachments; the local synthetic mode is explicit and forbidden in production.
Clinical rules, notifications, parent access and AI remain planned.
No prescribing, growth reference calculations or vaccination recommendations exist. TLS/encryption,
restricted DB role, external audit integrity, backup/restore, privacy review and clinical sign-off remain release gates.
