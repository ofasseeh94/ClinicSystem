import hashlib
import json
from uuid import UUID

from psycopg.types.json import Jsonb

from ..errors import Problem
from . import audit, forms
from . import repository as repo


def create(conn, principal, data, key: UUID):
    principal.require("patient:create")
    audit.lock_clinic(conn, principal.clinic_id)
    digest = hashlib.sha256(audit.canonical(data.model_dump(mode="json")).encode()).hexdigest()
    prior = conn.execute(
        "SELECT request_hash,response FROM idempotency_keys WHERE clinic_id=%s AND actor=%s AND key=%s",
        (principal.clinic_id, principal.actor_id, key),
    ).fetchone()
    if prior:
        if prior["request_hash"] != digest:
            raise Problem(
                409, "idempotency_conflict", "This request key was already used for different data."
            )
        audit.append(
            conn, principal, "patient.create_replay", UUID(prior["response"]["patient_id"])
        )
        return prior["response"]
    if data.background:
        principal.require("form:write")
        forms.validate_submission(conn, data.background)
    candidates = repo.duplicates(conn, principal.clinic_id, data)
    if candidates and not data.duplicate_review_reason:
        raise Problem(
            409,
            "duplicate_candidate",
            "Review possible existing records before creating another patient.",
            candidates=json.loads(audit.canonical(candidates)),
        )
    patient_id = repo.insert_patient(conn, principal, data)
    if data.background:
        repo.insert_form(conn, principal, patient_id, data.background)
    result = repo.patient(conn, principal.clinic_id, patient_id)
    audit.append(
        conn,
        principal,
        "patient.create",
        patient_id,
        after=result,
        reason=data.duplicate_review_reason,
    )
    conn.execute(
        "INSERT INTO idempotency_keys(clinic_id,actor,key,request_hash,patient_id,response) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (
            principal.clinic_id,
            principal.actor_id,
            key,
            digest,
            patient_id,
            Jsonb(json.loads(audit.canonical(result))),
        ),
    )
    return result


def update(conn, principal, patient_id, data, version):
    principal.require("patient:edit")
    audit.lock_clinic(conn, principal.clinic_id)
    before = repo.patient(conn, principal.clinic_id, patient_id)
    if before["version"] != version:
        raise Problem(
            412, "version_conflict", "This record changed. Reload it before saving your correction."
        )
    repo.update_patient(conn, principal, patient_id, data)
    result = repo.patient(conn, principal.clinic_id, patient_id)
    audit.append(
        conn,
        principal,
        "patient.update",
        patient_id,
        before=before,
        after=result,
        reason=data.audit_reason,
    )
    return result


def submit_form(conn, principal, patient_id, submission, version):
    principal.require("form:write")
    audit.lock_clinic(conn, principal.clinic_id)
    before = repo.patient(conn, principal.clinic_id, patient_id)
    if before["version"] != version:
        raise Problem(
            412,
            "version_conflict",
            "This record changed. Reload it before saving background history.",
        )
    forms.validate_submission(conn, submission)
    repo.insert_form(conn, principal, patient_id, submission)
    conn.execute(
        "UPDATE patients SET version=version+1,updated_at=now(),updated_by=%s WHERE clinic_id=%s AND id=%s",
        (principal.actor_id, principal.clinic_id, patient_id),
    )
    result = repo.patient(conn, principal.clinic_id, patient_id)
    audit.append(
        conn, principal, "form.submit", patient_id, after=submission.model_dump(mode="json")
    )
    return result
