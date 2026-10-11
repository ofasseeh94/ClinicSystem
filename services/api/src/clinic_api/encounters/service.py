import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from ..errors import Problem
from ..registry import audit
from .schemas import EncounterRecord, Note

FIELDS = tuple(EncounterRecord.model_fields)


def digest(data):
    return hashlib.sha256(audit.canonical(data.model_dump(mode="json")).encode()).hexdigest()


def read(conn, principal, patient_id, encounter_id):
    row = conn.execute(
        "SELECT * FROM encounters WHERE clinic_id=%s AND patient_id=%s AND id=%s",
        (principal.clinic_id, patient_id, encounter_id),
    ).fetchone()
    if not row:
        raise Problem(404, "encounter_not_found", "Encounter was not found.")
    row["addenda"] = conn.execute(
        "SELECT id,reason,content,signed_by,signed_at FROM encounter_addenda "
        "WHERE clinic_id=%s AND encounter_id=%s ORDER BY signed_at,id",
        (principal.clinic_id, encounter_id),
    ).fetchall()
    for key in ("occurred_at", "created_at", "updated_at", "signed_at"):
        if row[key] is not None:
            row[key] = row[key].astimezone(timezone.utc)
    for addition in row["addenda"]:
        addition["signed_at"] = addition["signed_at"].astimezone(timezone.utc)
    return {key: row[key] for key in FIELDS}


def patient(conn, principal, patient_id):
    row = conn.execute(
        "SELECT dob,dob_precision,dob_source,version,status FROM patients WHERE clinic_id=%s AND id=%s",
        (principal.clinic_id, patient_id),
    ).fetchone()
    if not row:
        raise Problem(404, "patient_not_found", "Patient was not found.")
    return row


def create(conn, principal, patient_id, data):
    principal.require("encounter:write")
    audit.lock_clinic(conn, principal.clinic_id)
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,1))", (str(data.request_id),))
    previous = conn.execute("SELECT * FROM encounters WHERE id=%s", (data.request_id,)).fetchone()
    if previous:
        if (
            previous["clinic_id"] != principal.clinic_id
            or previous["patient_id"] != patient_id
            or previous["create_actor"] != principal.actor_id
            or previous["create_hash"] != digest(data)
        ):
            raise Problem(409, "request_conflict", "Use a new request ID for a different visit.")
        return previous["create_response"]
    p = patient(conn, principal, patient_id)
    if p["status"] != "active":
        raise Problem(409, "inactive_patient", "New visits require an active patient.")
    visit_date = data.occurred_at.astimezone(ZoneInfo("Africa/Cairo")).date()
    if visit_date < p["dob"]:
        raise Problem(422, "before_birth", "Visit must not precede the recorded birth-date anchor.")
    birth = {
        "dob": p["dob"].isoformat(),
        "precision": p["dob_precision"],
        "source": p["dob_source"],
        "patient_version": p["version"],
        "age_days": (visit_date - p["dob"]).days if p["dob_precision"] == "exact" else None,
    }
    now = datetime.now(timezone.utc)
    snapshot = EncounterRecord(
        id=data.request_id,
        patient_id=patient_id,
        occurred_at=data.occurred_at.astimezone(timezone.utc),
        reason=data.reason,
        consent_context=data.consent_context,
        birth_context=birth,
        note=Note(),
        measurements=[],
        status="draft",
        version=1,
        created_by=principal.actor_id,
        updated_by=principal.actor_id,
        created_at=now,
        updated_at=now,
        signed_by=None,
        signed_at=None,
        cancellation_reason=None,
        addenda=[],
    ).model_dump(mode="json")
    conn.execute(
        "INSERT INTO encounters(id,clinic_id,patient_id,occurred_at,reason,consent_context,birth_context,"
        "note,created_by,updated_by,create_actor,create_hash,create_response,created_at,updated_at) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            data.request_id,
            principal.clinic_id,
            patient_id,
            data.occurred_at,
            data.reason,
            data.consent_context,
            Jsonb(birth),
            Jsonb(Note().model_dump()),
            principal.actor_id,
            principal.actor_id,
            principal.actor_id,
            digest(data),
            Jsonb(snapshot),
            now,
            now,
        ),
    )
    result = read(conn, principal, patient_id, data.request_id)
    audit.append(conn, principal, "encounter.create", data.request_id, after=result)
    return result


def change(conn, principal, patient_id, encounter_id, version, data, transition=False):
    principal.require("encounter:write")
    audit.lock_clinic(conn, principal.clinic_id)
    before = read(conn, principal, patient_id, encounter_id)
    if before["version"] != version:
        raise Problem(412, "stale_version", "This visit changed. Reload before saving.")
    if before["status"] in {"signed", "cancelled"}:
        raise Problem(
            409, "final_record", "Final visits cannot be edited; signed visits accept addenda."
        )
    if transition:
        allowed = {
            "draft": {"in_review", "cancelled"},
            "in_review": {"draft", "signed", "cancelled"},
        }
        if data.status not in allowed[before["status"]]:
            raise Problem(409, "invalid_transition", "This status transition is unavailable.")
        if data.status == "signed":
            note = before["note"]
            if (
                not all(note[k].strip() for k in ("history", "examination", "assessment", "plan"))
                or note["allergy_review"] != "reviewed"
                or note["medication_review"] != "reviewed"
            ):
                raise Problem(
                    422,
                    "incomplete_note",
                    "Complete all note sections and document allergy and medication review before signing.",
                )
        conn.execute(
            "UPDATE encounters SET status=%s,version=version+1,updated_by=%s,updated_at=now(),"
            "signed_by=CASE WHEN %s='signed' THEN %s ELSE NULL END,"
            "signed_at=CASE WHEN %s='signed' THEN now() ELSE NULL END,"
            "cancellation_reason=CASE WHEN %s='cancelled' THEN %s ELSE NULL END "
            "WHERE clinic_id=%s AND id=%s",
            (
                data.status,
                principal.actor_id,
                data.status,
                principal.actor_id,
                data.status,
                data.status,
                data.reason,
                principal.clinic_id,
                encounter_id,
            ),
        )
        reason = data.reason
    else:
        if before["status"] != "draft":
            raise Problem(409, "review_locked", "Return this visit to draft before editing.")
        birth_date = before["birth_context"]["dob"]
        if any(
            m.measured_at.astimezone(ZoneInfo("Africa/Cairo")).date().isoformat() < birth_date
            for m in data.measurements
        ):
            raise Problem(
                422, "before_birth", "Measurements must not precede the birth-date anchor."
            )
        conn.execute(
            "UPDATE encounters SET note=%s,measurements=%s,version=version+1,updated_by=%s,updated_at=now() "
            "WHERE clinic_id=%s AND id=%s",
            (
                Jsonb(data.note.model_dump()),
                Jsonb([m.model_dump(mode="json") for m in data.measurements]),
                principal.actor_id,
                principal.clinic_id,
                encounter_id,
            ),
        )
        reason = data.audit_reason
    result = read(conn, principal, patient_id, encounter_id)
    audit.append(
        conn,
        principal,
        "encounter.transition" if transition else "encounter.edit",
        encounter_id,
        before=before,
        after=result,
        reason=reason,
    )
    return result


def addendum(conn, principal, patient_id, encounter_id, data):
    principal.require("encounter:write")
    audit.lock_clinic(conn, principal.clinic_id)
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,1))", (str(data.request_id),))
    before = read(conn, principal, patient_id, encounter_id)
    if before["status"] != "signed":
        raise Problem(409, "unsigned_parent", "Addenda require a signed encounter.")
    previous = conn.execute(
        "SELECT * FROM encounter_addenda WHERE id=%s", (data.request_id,)
    ).fetchone()
    if previous:
        if (
            previous["clinic_id"] != principal.clinic_id
            or previous["encounter_id"] != encounter_id
            or previous["signed_by"] != principal.actor_id
            or previous["request_hash"] != digest(data)
        ):
            raise Problem(409, "request_conflict", "Use a new request ID for a different addendum.")
        return before
    conn.execute(
        "INSERT INTO encounter_addenda(id,clinic_id,encounter_id,reason,content,signed_by,request_hash) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s)",
        (
            data.request_id,
            principal.clinic_id,
            encounter_id,
            data.reason,
            data.content,
            principal.actor_id,
            digest(data),
        ),
    )
    result = read(conn, principal, patient_id, encounter_id)
    audit.append(
        conn, principal, "encounter.addendum", encounter_id, after=result, reason=data.reason
    )
    return result
