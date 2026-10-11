import hashlib
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from clinic_api.database import apply_migrations
from clinic_api.registry.audit import canonical
from conftest import ROOT
from fastapi.testclient import TestClient


def register(client, headers, data):
    result = client.post("/v1/patients", headers=headers, json=data)
    assert result.status_code == 201, result.text
    return result


def test_register_reopen_search_correct_audit(registry, headers, patient_data):
    client, settings = registry
    created = register(client, headers, patient_data)
    row = created.json()
    assert row["clinic_code"].startswith("PC-")
    assert row["contact_authority"] == "unverified"
    assert row["allergy_review_status"] == "unknown"
    assert row["warnings"]
    reopened = client.get(f"/v1/patients/{row['patient_id']}", headers=headers)
    assert reopened.json() == row
    assert reopened.headers["ETag"] == '"1"'
    for query in (
        "احمد",
        "SYNTHETIC ahmed",
        "حمودي",
        "+201000000001",
        "Synthetic Guardian",
        row["clinic_code"],
    ):
        result = client.post("/v1/patients/search", headers=headers, json={"query": query})
        assert result.status_code == 200
        assert result.json()["total"] == 1
        assert [ord(c) for c in result.json()["items"][0]["masked_phone"]] == [
            8226,
            8226,
            8226,
            8226,
            32,
            48,
            48,
            48,
            49,
        ]
        assert "phone_e164" not in result.json()["items"][0]
    corrected = client.patch(
        f"/v1/patients/{row['patient_id']}",
        headers={**headers, "If-Match": '"1"'},
        json={
            **patient_data,
            "name_en": "Synthetic Corrected",
            "audit_reason": "Correct guardian-reported spelling",
        },
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["version"] == 2
    stale = client.patch(
        f"/v1/patients/{row['patient_id']}",
        headers={**headers, "If-Match": '"1"'},
        json={**patient_data, "audit_reason": "Old concurrent correction"},
    )
    assert stale.status_code == 412
    events = client.get(
        "/v1/audit", headers=headers, params={"entity_id": row["patient_id"]}
    ).json()["items"]
    change = next(e for e in events if e["payload"]["action"] == "patient.update")
    assert change["payload"]["before"]["name_en"] == "Synthetic Ahmed"
    assert change["payload"]["after"]["name_en"] == "Synthetic Corrected"
    with psycopg.connect(settings.database_url) as conn:
        chain = conn.execute(
            "SELECT payload,previous_hash,event_hash FROM audit_events WHERE clinic_id=%s ORDER BY sequence",
            (settings.dev_clinic_id,),
        ).fetchall()
        previous = "0" * 64
        for payload, prev, digest in chain:
            assert prev == previous
            assert hashlib.sha256(canonical(payload).encode()).hexdigest() == digest
            previous = digest


def test_duplicate_review_idempotency_and_siblings(registry, headers, patient_data):
    client, _ = registry
    first = register(client, headers, patient_data).json()
    replay = register(client, headers, patient_data).json()
    assert replay == first
    conflict = client.post(
        "/v1/patients", headers=headers, json={**patient_data, "name_en": "Different test"}
    )
    assert conflict.status_code == 409 and conflict.json()["title"] == "idempotency_conflict"
    another = {**headers, "Idempotency-Key": str(uuid4())}
    duplicate = client.post("/v1/patients", headers=another, json=patient_data)
    assert duplicate.status_code == 409
    assert duplicate.json()["title"] == "duplicate_candidate"
    assert duplicate.json()["candidates"][0]["patient_id"] == first["patient_id"]
    approved = register(
        client,
        another,
        {**patient_data, "duplicate_review_reason": "Reviewed: separate synthetic twin record"},
    )
    assert approved.json()["patient_id"] != first["patient_id"]
    sibling = register(
        client,
        {**headers, "Idempotency-Key": str(uuid4())},
        {
            **patient_data,
            "name_ar": "شقيق تجريبي",
            "name_en": "Synthetic Sibling",
            "dob": "2021-01-01",
        },
    )
    assert sibling.json()["guardian"]["phone_e164"] == first["guardian"]["phone_e164"]


def test_invalid_background_is_atomic_and_versions_survive(registry, headers, patient_data):
    client, settings = registry
    invalid = client.post(
        "/v1/patients",
        headers=headers,
        json={
            **patient_data,
            "background": {
                "form_key": "background",
                "version": 1,
                "answers": {"birth.ga_weeks": "thirty"},
            },
        },
    )
    assert invalid.status_code == 422
    with psycopg.connect(settings.database_url) as conn:
        for table in (
            "patients",
            "contacts",
            "patient_contacts",
            "audit_events",
            "idempotency_keys",
        ):
            assert (
                conn.execute(
                    f"SELECT count(*) FROM {table} WHERE clinic_id=%s", (settings.dev_clinic_id,)
                ).fetchone()[0]
                == 0
            )
    first = register(
        client,
        headers,
        {
            **patient_data,
            "background": {
                "form_key": "background",
                "version": 1,
                "answers": {"birth.nicu": "unknown", "birth.weight_kg": 2.5},
            },
        },
    ).json()
    form2 = client.get("/v1/forms/background/versions/2", headers=headers)
    assert any(f["key"] == "birth.ventilation" for f in form2.json()["schema"]["fields"])
    result = client.post(
        f"/v1/patients/{first['patient_id']}/form-responses",
        headers={**headers, "If-Match": '"1"'},
        json={"form_key": "background", "version": 2, "answers": {"birth.ventilation": "no"}},
    )
    assert result.status_code == 201, result.text
    responses = result.json()["background_responses"]
    assert [r["version"] for r in responses] == [1, 2]
    assert responses[0]["answers"] == first["background_responses"][0]["answers"]
    assert result.json()["version"] == 2
    for table in ("audit_events", "form_definitions", "form_responses"):
        with (
            pytest.raises(psycopg.errors.RaiseException),
            psycopg.connect(settings.database_url) as conn,
        ):
            conn.execute(
                f"UPDATE {table} SET created_at=created_at"
                if table != "form_definitions"
                else "UPDATE form_definitions SET schema=schema"
            )


def test_uncertain_dates_and_known_allergies(registry, headers, patient_data):
    client, _ = registry
    row = register(
        client,
        headers,
        {
            **patient_data,
            "dob_precision": "year",
            "growth_reference_sex": "unknown",
            "allergy_review_status": "known",
            "allergies": [{"substance": "Synthetic ingredient", "reaction": "Reported rash"}],
        },
    ).json()
    assert row["dob_precision"] == "year" and row["allergies"][0]["reaction"] == "Reported rash"
    assert any("uncertain" in warning for warning in row["warnings"])


def test_concurrent_create_same_key_is_one_transaction(registry, headers, patient_data):
    client, settings = registry

    def create():
        with TestClient(client.app) as other:
            return other.post("/v1/patients", headers=headers, json=patient_data)

    with ThreadPoolExecutor(max_workers=3) as executor:
        responses = list(executor.map(lambda _: create(), range(3)))
    assert all(r.status_code == 201 for r in responses)
    assert len({r.json()["patient_id"] for r in responses}) == 1
    with psycopg.connect(settings.database_url) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM patients WHERE clinic_id=%s", (settings.dev_clinic_id,)
            ).fetchone()[0]
            == 1
        )


def test_migrations_repeat_and_detect_drift(database_url, tmp_path):
    apply_migrations(database_url, ROOT / "db/migrations")
    source = ROOT / "db/migrations/001_registry.sql"
    (tmp_path / source.name).write_text(
        source.read_text() + "\n-- changed applied migration", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Applied migration changed"):
        apply_migrations(database_url, tmp_path)
