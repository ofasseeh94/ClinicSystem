import hashlib
from datetime import datetime, timezone

from ..errors import Problem
from ..records.service import lock, scope
from ..registry import audit
from .schemas import CatalogRecord, StatementRecord

CATALOG_FIELDS = (
    "product_name",
    "generic_name",
    "formulation",
    "strength_text",
    "route_text",
    "source_kind",
    "source_title",
    "source_publisher",
    "source_version",
    "source_url",
    "source_country",
    "source_checked_on",
)
STATEMENT_FIELDS = (
    "encounter_id",
    "catalog_version_id",
    "supersedes_id",
    "medication_name",
    "reported_instructions",
    "use_status",
    "recorded_for",
    "source",
    "reason",
)


def digest(data):
    return hashlib.sha256(audit.canonical(data.model_dump(mode="json")).encode()).hexdigest()


def public(row, model):
    result = {k: row.get(k) for k in model.model_fields}
    result["request_id"] = row["id"]
    for k, v in result.items():
        if isinstance(v, datetime):
            result[k] = v.astimezone(timezone.utc)
    return result


def catalog(conn, principal, version_id):
    row = conn.execute(
        "SELECT * FROM medication_catalog WHERE clinic_id=%s AND id=%s",
        (principal.clinic_id, version_id),
    ).fetchone()
    if not row:
        raise Problem(404, "catalog_not_found", "Catalog version was not found.")
    return row


def create_catalog(conn, settings, principal, data, catalog_id=None):
    principal.require("medication:catalog_write")
    if settings.environment == "production" and data.source_kind == "synthetic":
        raise Problem(409, "synthetic_catalog", "Synthetic catalog entries are development-only.")
    lock(conn, principal, data.request_id)
    old = conn.execute(
        "SELECT * FROM medication_catalog WHERE id=%s", (data.request_id,)
    ).fetchone()
    target = catalog_id or data.request_id
    if old:
        if (
            old["clinic_id"] != principal.clinic_id
            or old["catalog_id"] != target
            or old["created_by"] != principal.actor_id
            or old["request_hash"] != digest(data)
        ):
            raise Problem(
                409, "request_conflict", "Use a new request ID for different catalog data."
            )
        return public(old, CatalogRecord)
    version = 1
    if catalog_id:
        latest = conn.execute(
            "SELECT version FROM medication_catalog WHERE clinic_id=%s AND catalog_id=%s ORDER BY version DESC LIMIT 1",
            (principal.clinic_id, catalog_id),
        ).fetchone()
        if not latest:
            raise Problem(404, "catalog_not_found", "Catalog was not found.")
        version = latest["version"] + 1
    fields = ",".join(CATALOG_FIELDS)
    placeholders = ",".join(["%s"] * (len(CATALOG_FIELDS) + 7))
    conn.execute(
        f"INSERT INTO medication_catalog(id,clinic_id,catalog_id,version,{fields},created_by,request_hash,state) VALUES({placeholders})",
        (
            data.request_id,
            principal.clinic_id,
            target,
            version,
            *(getattr(data, k) for k in CATALOG_FIELDS),
            principal.actor_id,
            digest(data),
            "draft",
        ),
    )
    result = public(catalog(conn, principal, data.request_id), CatalogRecord)
    audit.append(conn, principal, "medication.catalog_version", data.request_id, after=result)
    return result


def transition(conn, settings, principal, version_id, revision, data):
    principal.require(
        "medication:catalog_verify"
        if data.state == "verified_identity"
        else "medication:catalog_write"
    )
    lock(conn, principal)
    row = catalog(conn, principal, version_id)
    if row["revision"] != revision:
        raise Problem(412, "stale_version", "This catalog revision changed. Reload first.")
    allowed = {
        "draft": {"in_review", "retired"},
        "in_review": {"draft", "verified_identity", "retired"},
        "verified_identity": {"retired"},
        "retired": set(),
    }
    if data.state not in allowed[row["state"]]:
        raise Problem(409, "catalog_transition", "This catalog transition is unavailable.")
    verifying = data.state == "verified_identity"
    if verifying:
        if settings.environment == "development":
            raise Problem(
                409,
                "managed_reviewer_required",
                "Identity verification requires distinct managed reviewers; development keys cannot approve it.",
            )
        if row["source_kind"] == "synthetic" or not row["source_url"]:
            raise Problem(
                409, "source_required", "A real cited source is required for identity verification."
            )
        if row["created_by"] == principal.actor_id:
            raise Problem(
                409,
                "independent_review",
                "A different qualified reviewer must verify this identity.",
            )
    conn.execute(
        "UPDATE medication_catalog SET state=%s,revision=revision+1,review_reason=%s,reviewed_by=CASE WHEN %s THEN %s ELSE reviewed_by END,reviewed_at=CASE WHEN %s THEN now() ELSE reviewed_at END WHERE clinic_id=%s AND id=%s",
        (
            data.state,
            data.reason,
            verifying,
            principal.actor_id,
            verifying,
            principal.clinic_id,
            version_id,
        ),
    )
    result = public(catalog(conn, principal, version_id), CatalogRecord)
    audit.append(
        conn,
        principal,
        "medication.catalog_review",
        version_id,
        before=public(row, CatalogRecord),
        after=result,
        reason=data.reason,
    )
    return result


def create_statement(conn, principal, patient_id, data):
    principal.require("medication:history_write")
    lock(conn, principal, data.request_id)
    old = conn.execute(
        "SELECT * FROM medication_statements WHERE id=%s", (data.request_id,)
    ).fetchone()
    if old:
        if (
            old["clinic_id"] != principal.clinic_id
            or old["patient_id"] != patient_id
            or old["created_by"] != principal.actor_id
            or old["request_hash"] != digest(data)
        ):
            raise Problem(
                409, "request_conflict", "Use a new request ID for different reported history."
            )
        return public(old, StatementRecord)
    scope(conn, principal, patient_id, data.encounter_id)
    if data.catalog_version_id:
        c = catalog(conn, principal, data.catalog_version_id)
        if c["state"] != "verified_identity":
            raise Problem(
                409,
                "catalog_unreviewed",
                "Only identity-verified catalog versions may be linked; free-text reported history is available.",
            )
    if data.supersedes_id:
        row = conn.execute(
            "SELECT * FROM medication_statements WHERE clinic_id=%s AND patient_id=%s AND id=%s",
            (principal.clinic_id, patient_id, data.supersedes_id),
        ).fetchone()
        if not row:
            raise Problem(
                404, "statement_not_found", "Reported medication was not found for this patient."
            )
        if conn.execute(
            "SELECT id FROM medication_statements WHERE clinic_id=%s AND supersedes_id=%s",
            (principal.clinic_id, data.supersedes_id),
        ).fetchone():
            raise Problem(
                409, "already_corrected", "Correct the latest statement in this history chain."
            )
    fields = ",".join(STATEMENT_FIELDS)
    placeholders = ",".join(["%s"] * (len(STATEMENT_FIELDS) + 5))
    row = conn.execute(
        f"INSERT INTO medication_statements(id,clinic_id,patient_id,{fields},created_by,request_hash) VALUES({placeholders}) RETURNING *",
        (
            data.request_id,
            principal.clinic_id,
            patient_id,
            *(getattr(data, k) for k in STATEMENT_FIELDS),
            principal.actor_id,
            digest(data),
        ),
    ).fetchone()
    result = public(row, StatementRecord)
    audit.append(
        conn,
        principal,
        "medication.history_correction" if data.supersedes_id else "medication.reported_history",
        data.request_id,
        after=result,
        reason=data.reason,
    )
    return result
