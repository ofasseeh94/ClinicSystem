import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from ..errors import Problem
from ..registry import audit
from . import files
from .schemas import DocumentRecord, OrderRecord, ResultRecord

TABLES = {
    "document": "documents",
    "order": "investigation_orders",
    "result": "investigation_results",
}
MODELS = {"document": DocumentRecord, "order": OrderRecord, "result": ResultRecord}


def scope(conn, principal, patient_id, encounter_id=None):
    if not conn.execute(
        "SELECT id FROM patients WHERE clinic_id=%s AND id=%s", (principal.clinic_id, patient_id)
    ).fetchone():
        raise Problem(404, "patient_not_found", "Patient was not found.")
    if encounter_id:
        row = conn.execute(
            "SELECT status FROM encounters WHERE clinic_id=%s AND patient_id=%s AND id=%s",
            (principal.clinic_id, patient_id, encounter_id),
        ).fetchone()
        if not row:
            raise Problem(404, "encounter_not_found", "Encounter was not found for this patient.")
        if row["status"] == "cancelled":
            raise Problem(
                409, "cancelled_encounter", "New records cannot link a cancelled encounter."
            )


def raw(conn, principal, patient_id, kind, record_id):
    row = conn.execute(
        f"SELECT * FROM {TABLES[kind]} WHERE clinic_id=%s AND patient_id=%s AND id=%s",
        (principal.clinic_id, patient_id, record_id),
    ).fetchone()
    if not row:
        raise Problem(404, "record_not_found", "Record was not found for this patient.")
    return row


def public(row, kind):
    result = {k: row.get(k) for k in MODELS[kind].model_fields}
    for k, v in result.items():
        if isinstance(v, datetime):
            result[k] = v.astimezone(timezone.utc)
    return result


def lock(conn, principal, request_id=None):
    audit.lock_clinic(conn, principal.clinic_id)
    if request_id:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,2))", (str(request_id),))


def request_hash(data):
    return hashlib.sha256(audit.canonical(data.model_dump(mode="json")).encode()).hexdigest()


def replay(conn, principal, patient_id, kind, data):
    row = conn.execute(f"SELECT * FROM {TABLES[kind]} WHERE id=%s", (data.request_id,)).fetchone()
    if row:
        if (
            row["clinic_id"] != principal.clinic_id
            or row["patient_id"] != patient_id
            or row["created_by"] != principal.actor_id
            or row["request_hash"] != request_hash(data)
        ):
            raise Problem(409, "request_conflict", "Use a new request ID for different data.")
        return public(row, kind)


def create_document(conn, settings, principal, patient_id, data):
    principal.require("document:write")
    files.key(settings)
    lock(conn, principal, data.request_id)
    existing = replay(conn, principal, patient_id, "document", data)
    if existing:
        return existing
    scope(conn, principal, patient_id, data.encounter_id)
    conn.execute(
        "INSERT INTO documents(id,clinic_id,patient_id,encounter_id,title,category,captured_at,source,created_by,request_hash) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            data.request_id,
            principal.clinic_id,
            patient_id,
            data.encounter_id,
            data.title,
            data.category,
            data.captured_at,
            data.source,
            principal.actor_id,
            request_hash(data),
        ),
    )
    result = public(raw(conn, principal, patient_id, "document", data.request_id), "document")
    audit.append(conn, principal, "document.create", data.request_id, after=result)
    return result


def upload(conn, settings, principal, patient_id, document_id, content, mime):
    principal.require("document:write")
    files.validate(content, mime)
    lock(conn, principal)
    row = raw(conn, principal, patient_id, "document", document_id)
    digest = hashlib.sha256(content).hexdigest()
    if row["encrypted_content"] is not None:
        if row["state"] != "withdrawn" and row["sha256"] == digest and row["mime_type"] == mime:
            return public(row, "document")
        raise Problem(
            409,
            "immutable_content",
            "Existing attachments cannot be replaced. Create a new record.",
        )
    if row["state"] != "pending_upload":
        raise Problem(409, "upload_closed", "This upload is no longer available.")
    encrypted = files.encrypt(settings, content, principal.clinic_id, document_id)
    state, detail = files.scan(settings, content)
    conn.execute(
        "UPDATE documents SET encrypted_content=%s,mime_type=%s,byte_size=%s,sha256=%s,state=%s,scan_detail=%s,version=version+1 "
        "WHERE clinic_id=%s AND id=%s",
        (encrypted, mime, len(content), digest, state, detail, principal.clinic_id, document_id),
    )
    scan_event(conn, principal, document_id, state, detail)
    result = public(raw(conn, principal, patient_id, "document", document_id), "document")
    audit.append(
        conn,
        principal,
        "document.upload",
        document_id,
        before=public(row, "document"),
        after=result,
    )
    return result


def scan_event(conn, principal, document_id, state, detail):
    conn.execute(
        "INSERT INTO document_scans(id,clinic_id,document_id,state,detail,actor) VALUES(%s,%s,%s,%s,%s,%s)",
        (uuid4(), principal.clinic_id, document_id, state, detail, principal.actor_id),
    )


def change_document(conn, settings, principal, patient_id, document_id, version, reason, withdraw):
    principal.require("document:write")
    lock(conn, principal)
    row = raw(conn, principal, patient_id, "document", document_id)
    if row["version"] != version:
        raise Problem(412, "stale_version", "This record changed. Reload before continuing.")
    if row["state"] == "withdrawn":
        raise Problem(409, "withdrawn_document", "Withdrawn attachments cannot be changed.")
    if withdraw:
        state, detail = "withdrawn", row["scan_detail"]
    else:
        if row["state"] not in {"quarantined", "synthetic_ready"}:
            raise Problem(
                409,
                "scan_unavailable",
                "Only quarantined or development attachments can be rescanned.",
            )
        content = files.decrypt(
            settings,
            bytes(row["encrypted_content"]),
            principal.clinic_id,
            document_id,
            row["sha256"],
        )
        state, detail = files.scan(settings, content)
        scan_event(conn, principal, document_id, state, detail)
    conn.execute(
        "UPDATE documents SET state=%s,scan_detail=%s,withdrawal_reason=%s,version=version+1 WHERE clinic_id=%s AND id=%s",
        (state, detail, reason if withdraw else None, principal.clinic_id, document_id),
    )
    result = public(raw(conn, principal, patient_id, "document", document_id), "document")
    audit.append(
        conn,
        principal,
        "document.withdraw" if withdraw else "document.rescan",
        document_id,
        before=public(row, "document"),
        after=result,
        reason=reason,
    )
    return result


def readable(settings, row):
    if not (
        row["state"] == "ready"
        or (row["state"] == "synthetic_ready" and settings.environment in {"development", "test"})
    ):
        raise Problem(
            409,
            "document_not_released",
            "Attachment retrieval is blocked by its lifecycle/scanning state.",
        )


def ticket_key(settings):
    return hashlib.sha256(b"clinic-document-ticket-v1" + files.key(settings)).digest()


def ticket(conn, settings, principal, patient_id, document_id):
    principal.require("document:read")
    lock(conn, principal)
    row = raw(conn, principal, patient_id, "document", document_id)
    readable(settings, row)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": principal.actor_id,
            "clinic": str(principal.clinic_id),
            "patient": str(patient_id),
            "document": str(document_id),
            "hash": row["sha256"],
            "iat": now,
            "exp": now + timedelta(seconds=60),
            "aud": "clinic-document-download",
        },
        ticket_key(settings),
        algorithm="HS256",
    )
    audit.append(conn, principal, "document.ticket", document_id)
    return {"ticket": token, "expires_in": 60}


def download(conn, settings, principal, patient_id, document_id, token):
    principal.require("document:read")
    lock(conn, principal)
    try:
        claims = jwt.decode(
            token,
            ticket_key(settings),
            algorithms=["HS256"],
            audience="clinic-document-download",
            options={"require": ["sub", "clinic", "patient", "document", "hash", "iat", "exp"]},
        )
        if (claims["sub"], claims["clinic"], claims["patient"], claims["document"]) != (
            principal.actor_id,
            str(principal.clinic_id),
            str(patient_id),
            str(document_id),
        ):
            raise ValueError("Wrong scope")
    except (jwt.PyJWTError, ValueError, KeyError):
        raise Problem(
            403, "invalid_ticket", "This document ticket is invalid or expired. Request a new one."
        ) from None
    row = raw(conn, principal, patient_id, "document", document_id)
    readable(settings, row)
    if claims["hash"] != row["sha256"]:
        raise Problem(403, "invalid_ticket", "This document ticket does not match the attachment.")
    content = files.decrypt(
        settings, bytes(row["encrypted_content"]), principal.clinic_id, document_id, row["sha256"]
    )
    audit.append(conn, principal, "document.download", document_id, after={"sha256": row["sha256"]})
    return content, row["mime_type"]


def create_order(conn, principal, patient_id, data):
    principal.require("investigation:write")
    lock(conn, principal, data.request_id)
    existing = replay(conn, principal, patient_id, "order", data)
    if existing:
        return existing
    scope(conn, principal, patient_id, data.encounter_id)
    conn.execute(
        "INSERT INTO investigation_orders(id,clinic_id,patient_id,encounter_id,test_name,indication,priority,created_by,updated_by,request_hash) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            data.request_id,
            principal.clinic_id,
            patient_id,
            data.encounter_id,
            data.test_name,
            data.indication,
            data.priority,
            principal.actor_id,
            principal.actor_id,
            request_hash(data),
        ),
    )
    result = public(raw(conn, principal, patient_id, "order", data.request_id), "order")
    audit.append(conn, principal, "investigation.order", data.request_id, after=result)
    return result


def change_order(conn, principal, patient_id, order_id, version, data):
    principal.require("investigation:write")
    lock(conn, principal)
    row = raw(conn, principal, patient_id, "order", order_id)
    if row["version"] != version:
        raise Problem(412, "stale_version", "This order changed. Reload before continuing.")
    if row["status"] in {"completed", "cancelled"} or row["status"] == data.status:
        raise Problem(409, "final_order", "This order transition is unavailable.")
    if (
        data.status == "completed"
        and not conn.execute(
            "SELECT id FROM investigation_results WHERE clinic_id=%s AND order_id=%s LIMIT 1",
            (principal.clinic_id, order_id),
        ).fetchone()
    ):
        raise Problem(422, "result_required", "Record a result before completing the order.")
    conn.execute(
        "UPDATE investigation_orders SET status=%s,cancellation_reason=%s,version=version+1,updated_by=%s,updated_at=now() WHERE clinic_id=%s AND id=%s",
        (
            data.status,
            data.reason if data.status == "cancelled" else None,
            principal.actor_id,
            principal.clinic_id,
            order_id,
        ),
    )
    result = public(raw(conn, principal, patient_id, "order", order_id), "order")
    audit.append(
        conn,
        principal,
        "investigation.status",
        order_id,
        before=public(row, "order"),
        after=result,
        reason=data.reason,
    )
    return result


def create_result(conn, settings, principal, patient_id, data):
    principal.require("investigation:write")
    lock(conn, principal, data.request_id)
    existing = replay(conn, principal, patient_id, "result", data)
    if existing:
        return existing
    scope(conn, principal, patient_id)
    if data.order_id:
        order = raw(conn, principal, patient_id, "order", data.order_id)
        if order["status"] == "cancelled":
            raise Problem(409, "cancelled_order", "Results cannot link a cancelled order.")
    if data.document_id:
        doc = raw(conn, principal, patient_id, "document", data.document_id)
        readable(settings, doc)
    if data.supersedes_id:
        previous = raw(conn, principal, patient_id, "result", data.supersedes_id)
        if previous["order_id"] != data.order_id:
            raise Problem(
                409, "correction_scope", "A correction must retain the original order link."
            )
        if conn.execute(
            "SELECT id FROM investigation_results WHERE clinic_id=%s AND supersedes_id=%s",
            (principal.clinic_id, data.supersedes_id),
        ).fetchone():
            raise Problem(
                409, "already_corrected", "Correct the latest result in this correction chain."
            )
    conn.execute(
        "INSERT INTO investigation_results(id,clinic_id,patient_id,order_id,document_id,supersedes_id,test_name,collected_at,value,unit,reference_range,interpretation,source,reason,created_by,request_hash) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            data.request_id,
            principal.clinic_id,
            patient_id,
            data.order_id,
            data.document_id,
            data.supersedes_id,
            data.test_name,
            data.collected_at,
            data.value,
            data.unit,
            data.reference_range,
            data.interpretation,
            data.source,
            data.reason,
            principal.actor_id,
            request_hash(data),
        ),
    )
    result = public(raw(conn, principal, patient_id, "result", data.request_id), "result")
    audit.append(
        conn,
        principal,
        "investigation.result_correction" if data.supersedes_id else "investigation.result",
        data.request_id,
        after=result,
        reason=data.reason,
    )
    return result
