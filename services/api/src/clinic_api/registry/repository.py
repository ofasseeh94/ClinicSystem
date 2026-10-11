"""Parameterized PostgreSQL queries; every patient query is clinic-scoped."""

from uuid import uuid4

from psycopg.types.json import Jsonb

from ..errors import Problem
from .normalization import normalize


def patient(conn, clinic_id, patient_id):
    row = conn.execute(
        "SELECT * FROM patients WHERE clinic_id=%s AND id=%s", (clinic_id, patient_id)
    ).fetchone()
    if not row:
        raise Problem(404, "patient_not_found", "Patient record was not found.")
    contact = conn.execute(
        "SELECT c.*,pc.relation,pc.authority_status FROM contacts c JOIN patient_contacts pc "
        "ON c.id=pc.contact_id AND c.clinic_id=pc.clinic_id "
        "WHERE pc.clinic_id=%s AND pc.patient_id=%s ORDER BY pc.created_at LIMIT 1",
        (clinic_id, patient_id),
    ).fetchone()
    aliases = conn.execute(
        "SELECT alias FROM patient_aliases WHERE clinic_id=%s AND patient_id=%s "
        "ORDER BY created_at,id",
        (clinic_id, patient_id),
    ).fetchall()
    allergies = conn.execute(
        "SELECT substance,reaction FROM allergies WHERE clinic_id=%s AND patient_id=%s "
        "AND state='active' ORDER BY created_at,id",
        (clinic_id, patient_id),
    ).fetchall()
    forms = conn.execute(
        "SELECT r.id,r.form_key,r.form_version AS version,r.answers,r.created_at,r.created_by,fd.schema AS schema_definition "
        "FROM form_responses r JOIN form_definitions fd ON fd.form_key=r.form_key AND fd.version=r.form_version "
        "WHERE r.clinic_id=%s AND r.patient_id=%s ORDER BY r.created_at,r.id",
        (clinic_id, patient_id),
    ).fetchall()
    warnings = []
    if row["allergy_review_status"] in {"unknown", "not_assessed"}:
        warnings.append("Allergy history requires review")
    if row["dob_precision"] != "exact":
        warnings.append("Birth date is uncertain; exact age calculations are unavailable")
    return {
        "patient_id": row["id"],
        **{
            k: row[k]
            for k in (
                "clinic_code",
                "name_ar",
                "name_en",
                "dob",
                "dob_precision",
                "dob_source",
                "growth_reference_sex",
                "allergy_review_status",
                "version",
                "created_at",
                "updated_at",
                "created_by",
                "updated_by",
                "status",
            )
        },
        "guardian": {
            "name": contact["name"],
            "phone_e164": contact["phone_e164"],
            "relation": contact["relation"],
        },
        "contact_authority": contact["authority_status"],
        "aliases": [a["alias"] for a in aliases],
        "allergies": allergies,
        "background_responses": forms,
        "warnings": warnings,
    }


def summary(row):
    return {
        "patient_id": row["id"],
        **{
            k: row[k]
            for k in (
                "clinic_code",
                "name_ar",
                "name_en",
                "dob",
                "dob_precision",
                "growth_reference_sex",
                "allergy_review_status",
                "version",
            )
        },
        "guardian_name": row["guardian_name"],
        "masked_phone": "\u2022" * 4 + " " + row["phone_e164"][-4:],
    }


JOIN = (
    " FROM patients p JOIN patient_contacts pc ON p.id=pc.patient_id AND p.clinic_id=pc.clinic_id "
    "JOIN contacts c ON c.id=pc.contact_id AND c.clinic_id=pc.clinic_id "
)
SELECT = "SELECT p.*,c.name AS guardian_name,c.phone_e164 "


def search(conn, clinic_id, request):
    query = normalize(request.query)
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    where = (
        "WHERE p.clinic_id=%s AND (p.normalized_names LIKE %s OR lower(p.clinic_code) LIKE %s "
        "OR c.normalized_name LIKE %s OR c.phone_e164 LIKE %s OR EXISTS "
        "(SELECT 1 FROM patient_aliases a WHERE a.patient_id=p.id AND a.clinic_id=p.clinic_id "
        "AND a.normalized_alias LIKE %s))"
    )
    params = (clinic_id, pattern, pattern, pattern, pattern, pattern)
    total = conn.execute("SELECT count(*) " + JOIN + where, params).fetchone()["count"]
    rows = conn.execute(
        SELECT + JOIN + where + " ORDER BY p.created_at DESC,p.id LIMIT %s OFFSET %s",
        (*params, request.page_size, (request.page - 1) * request.page_size),
    ).fetchall()
    return {
        "items": [summary(r) for r in rows],
        "total": total,
        "page": request.page,
        "page_size": request.page_size,
    }


def duplicates(conn, clinic_id, data):
    # Shared guardian alone is not a duplicate: DOB plus exact name/phone requires deliberate review.
    rows = conn.execute(
        SELECT + JOIN + "WHERE p.clinic_id=%s AND p.dob=%s AND "
        "((%s<>'' AND p.name_ar<>'' AND split_part(p.normalized_names,' | ',1)=%s) "
        "OR (%s<>'' AND p.name_en<>'' AND split_part(p.normalized_names,' | ',2)=%s) OR c.phone_e164=%s) "
        "ORDER BY p.created_at LIMIT 20",
        (
            clinic_id,
            data.dob,
            normalize(data.name_ar),
            normalize(data.name_ar),
            normalize(data.name_en),
            normalize(data.name_en),
            data.guardian.phone_e164,
        ),
    ).fetchall()
    return [summary(r) for r in rows]


def replace_details(conn, principal, patient_id, data):
    # Alias and allergy prior values remain in restricted immutable audit snapshots.
    conn.execute(
        "DELETE FROM patient_aliases WHERE clinic_id=%s AND patient_id=%s",
        (principal.clinic_id, patient_id),
    )
    for alias in data.aliases:
        conn.execute(
            "INSERT INTO patient_aliases(id,clinic_id,patient_id,alias,normalized_alias,created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (uuid4(), principal.clinic_id, patient_id, alias, normalize(alias), principal.actor_id),
        )
    conn.execute(
        "UPDATE allergies SET state='superseded' WHERE clinic_id=%s AND patient_id=%s AND state='active'",
        (principal.clinic_id, patient_id),
    )
    for allergy in data.allergies:
        conn.execute(
            "INSERT INTO allergies(id,clinic_id,patient_id,substance,reaction,created_by) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                uuid4(),
                principal.clinic_id,
                patient_id,
                allergy.substance,
                allergy.reaction,
                principal.actor_id,
            ),
        )


def insert_patient(conn, principal, data):
    patient_id, contact_id = uuid4(), uuid4()
    code = conn.execute("SELECT nextval('patient_code_sequence') AS n").fetchone()["n"]
    conn.execute(
        "INSERT INTO patients(id,clinic_id,clinic_code,name_ar,name_en,normalized_names,dob,dob_precision,"
        "dob_source,growth_reference_sex,allergy_review_status,created_by,updated_by) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            patient_id,
            principal.clinic_id,
            f"PC-{code:06d}",
            data.name_ar,
            data.name_en,
            normalize(data.name_ar) + " | " + normalize(data.name_en),
            data.dob,
            data.dob_precision,
            data.dob_source,
            data.growth_reference_sex,
            data.allergy_review_status,
            principal.actor_id,
            principal.actor_id,
        ),
    )
    # No automatic guardian merge or authority inference from a matching phone number.
    conn.execute(
        "INSERT INTO contacts(id,clinic_id,name,normalized_name,phone_e164,created_by,updated_by) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (
            contact_id,
            principal.clinic_id,
            data.guardian.name,
            normalize(data.guardian.name),
            data.guardian.phone_e164,
            principal.actor_id,
            principal.actor_id,
        ),
    )
    conn.execute(
        "INSERT INTO patient_contacts(clinic_id,patient_id,contact_id,relation,created_by,updated_by) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (
            principal.clinic_id,
            patient_id,
            contact_id,
            data.guardian.relation,
            principal.actor_id,
            principal.actor_id,
        ),
    )
    replace_details(conn, principal, patient_id, data)
    return patient_id


def update_patient(conn, principal, patient_id, data):
    conn.execute(
        "UPDATE patients SET name_ar=%s,name_en=%s,normalized_names=%s,dob=%s,dob_precision=%s,dob_source=%s,"
        "growth_reference_sex=%s,allergy_review_status=%s,version=version+1,updated_at=now(),updated_by=%s "
        "WHERE clinic_id=%s AND id=%s",
        (
            data.name_ar,
            data.name_en,
            normalize(data.name_ar) + " | " + normalize(data.name_en),
            data.dob,
            data.dob_precision,
            data.dob_source,
            data.growth_reference_sex,
            data.allergy_review_status,
            principal.actor_id,
            principal.clinic_id,
            patient_id,
        ),
    )
    conn.execute(
        "UPDATE contacts c SET name=%s,normalized_name=%s,phone_e164=%s,verified_at=NULL,updated_at=now(),"
        "updated_by=%s FROM patient_contacts pc WHERE c.id=pc.contact_id AND c.clinic_id=pc.clinic_id "
        "AND pc.patient_id=%s AND pc.clinic_id=%s",
        (
            data.guardian.name,
            normalize(data.guardian.name),
            data.guardian.phone_e164,
            principal.actor_id,
            patient_id,
            principal.clinic_id,
        ),
    )
    conn.execute(
        "UPDATE patient_contacts SET relation=%s,authority_status='unverified',updated_at=now(),updated_by=%s "
        "WHERE patient_id=%s AND clinic_id=%s",
        (data.guardian.relation, principal.actor_id, patient_id, principal.clinic_id),
    )
    replace_details(conn, principal, patient_id, data)


def insert_form(conn, principal, patient_id, submission):
    response_id = uuid4()
    conn.execute(
        "INSERT INTO form_responses(id,clinic_id,patient_id,form_key,form_version,answers,created_by) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (
            response_id,
            principal.clinic_id,
            patient_id,
            submission.form_key,
            submission.version,
            Jsonb(submission.answers),
            principal.actor_id,
        ),
    )
    return response_id
