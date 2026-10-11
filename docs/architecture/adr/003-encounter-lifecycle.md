# ADR-003: preserve encounter snapshots and append corrections

Status: accepted for synthetic development, 2026-10-11.

Use the existing PostgreSQL and clinic audit transaction boundary. Store an encounter's current
structured narrative and raw measurement list in one versioned row; retain every replacement in
immutable before/after audit snapshots. This keeps the first clinical-record unit small without
pretending to provide diagnoses, orders or growth engines. A later query-heavy measurement module
may normalize observations with an additive migration that preserves signed JSON snapshots.

Only draft rows are editable. Review freezes entry until returned to draft. Signing requires
four narrative sections plus review acknowledgments, records the authenticated actor/server time,
and freezes the row through a database trigger. Cancellation also freezes the row with a reason.
Signed corrections append to a separate immutable addenda table. Independent addenda do not
change the parent's version; UUID replay prevents duplicate append on retries.

Birth context and visit time are saved once. Cairo calendar age is calculated for exact DOB;
uncertainty suppresses exact age. Later identity corrections cannot silently rewrite clinical history.
Per-clinic advisory transaction locks serialize audit/edit operations; request-ID locks also handle
colliding UUIDs across clinics. If-Match protects draft/status operations from lost updates.

Consequences: draft history is retrieved through restricted audit rather than a dedicated version UI.
JSON measurements are unsuitable for future population growth analytics without normalization.
Technical numeric bounds do not establish medical plausibility. The electronic staff attestation is
not a cryptographic signature or proof of production identity/consent/security compliance.
