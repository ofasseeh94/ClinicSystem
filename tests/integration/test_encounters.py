from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from clinic_api.auth import Principal, authenticate
from clinic_api.encounters.schemas import Measurement
from fastapi.testclient import TestClient
from pydantic import ValidationError


def setup_visit(registry, headers, patient_data):
    client, settings = registry
    p = client.post("/v1/patients", headers=headers, json=patient_data).json()
    base = f"/v1/patients/{p['patient_id']}/encounters"
    data = {
        "request_id": str(uuid4()),
        "occurred_at": "2025-05-01T10:00:00+03:00",
        "reason": "Synthetic follow-up",
        "consent_context": "Synthetic guardian present",
    }
    result = client.post(base, headers=headers, json=data)
    assert result.status_code == 201, result.text
    return client, settings, p, base, data, result.json()


def content():
    return {
        "note": {
            "history": "Synthetic history",
            "examination": "Synthetic examination",
            "assessment": "Synthetic assessment",
            "plan": "Synthetic plan",
            "allergy_review": "reviewed",
            "medication_review": "reviewed",
        },
        "measurements": [
            {
                "measured_at": "2025-05-01T10:00:00+03:00",
                "weight_kg": 12.3,
                "position": "standing",
                "technique": "Synthetic direct observation",
                "equipment": "Synthetic scale",
                "source": "clinic",
            }
        ],
        "audit_reason": "Document synthetic visit",
    }


def status(client, base, headers, record, target):
    return client.post(
        f"{base}/{record['id']}/status",
        headers={**headers, "If-Match": f'"{record["version"]}"'},
        json={"status": target, "reason": "Synthetic clinician review"},
    )


def test_encounter_lifecycle_immutable_addenda_replay(registry, headers, patient_data):
    client, settings, p, base, data, original = setup_visit(
        registry, headers, patient_data
    )
    url = f"{base}/{original['id']}"
    assert original["birth_context"]["age_days"] == 686
    assert status(client, base, headers, original, "signed").status_code == 409
    reviewed = status(client, base, headers, original, "in_review").json()
    assert status(client, base, headers, reviewed, "signed").status_code == 422
    assert (
        client.put(
            url, headers={**headers, "If-Match": '"2"'}, json=content()
        ).status_code
        == 409
    )
    draft = status(client, base, headers, reviewed, "draft").json()
    result = client.put(
        url, headers={**headers, "If-Match": f'"{draft["version"]}"'}, json=content()
    )
    assert result.status_code == 200, result.text
    edited = result.json()
    assert (
        client.put(
            url, headers={**headers, "If-Match": '"1"'}, json=content()
        ).status_code
        == 412
    )
    assert client.put(url, headers=headers, json=content()).status_code == 428
    review = status(client, base, headers, edited, "in_review").json()
    signed = status(client, base, headers, review, "signed").json()
    assert signed["signed_by"] == "synthetic-development-staff"
    assert signed["signed_at"]
    assert (
        client.put(
            url,
            headers={**headers, "If-Match": f'"{signed["version"]}"'},
            json=content(),
        ).status_code
        == 409
    )
    assert status(client, base, headers, signed, "cancelled").status_code == 409
    replay = client.post(base, headers=headers, json=data)
    assert replay.json() == original
    assert (
        client.post(
            base, headers=headers, json={**data, "reason": "Changed request"}
        ).status_code
        == 409
    )
    addition = {
        "request_id": str(uuid4()),
        "reason": "Correct synthetic observation",
        "content": "Synthetic addendum",
    }
    amended = client.post(url + "/addenda", headers=headers, json=addition)
    assert amended.status_code == 201, amended.text
    assert amended.json()["note"] == signed["note"]
    assert amended.json()["version"] == signed["version"]
    assert (
        len(
            client.post(url + "/addenda", headers=headers, json=addition).json()[
                "addenda"
            ]
        )
        == 1
    )
    assert (
        client.post(
            url + "/addenda", headers=headers, json={**addition, "content": "Different"}
        ).status_code
        == 409
    )
    for query in (
        ("UPDATE encounters SET reason='Changed' WHERE id=%s", signed["id"]),
        ("DELETE FROM encounters WHERE id=%s", signed["id"]),
        (
            "UPDATE encounter_addenda SET content='Changed' WHERE id=%s",
            addition["request_id"],
        ),
        ("DELETE FROM encounter_addenda WHERE id=%s", addition["request_id"]),
    ):
        with psycopg.connect(settings.database_url) as conn:
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(*query[:1], (query[1],))
            conn.rollback()
    events = client.get(
        "/v1/audit", headers=headers, params={"entity_id": signed["id"]}
    ).json()["items"]
    actions = [e["payload"]["action"] for e in events]
    assert (
        "encounter.create" in actions
        and "encounter.edit" in actions
        and "encounter.addendum" in actions
    )


def test_birth_context_measurements_validation_and_cancellation(
    registry, headers, patient_data
):
    client, settings, p, base, data, original = setup_visit(
        registry, headers, {**patient_data, "dob_precision": "estimated"}
    )
    assert original["birth_context"]["age_days"] is None
    url = f"{base}/{original['id']}"
    correction = client.patch(
        f"/v1/patients/{p['patient_id']}",
        headers={**headers, "If-Match": '"1"'},
        json={
            **patient_data,
            "dob": "2023-07-15",
            "audit_reason": "Correct synthetic birth date",
        },
    )
    assert correction.status_code == 200
    assert (
        client.get(url, headers=headers).json()["birth_context"]
        == original["birth_context"]
    )
    for measurement in (
        {},
        {**content()["measurements"][0], "weight_kg": -1},
        {**content()["measurements"][0], "measured_at": "2022-01-01T10:00:00Z"},
        {**content()["measurements"][0], "measured_at": "2025-01-01T10:00:00"},
    ):
        response = client.put(
            url,
            headers={**headers, "If-Match": '"1"'},
            json={**content(), "measurements": [measurement]},
        )
        assert response.status_code == 422, response.text
    for value in (
        "2020-01-01T00:00:00Z",
        "2025-01-01T10:00:00",
        (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    ):
        assert (
            client.post(
                base,
                headers=headers,
                json={**data, "request_id": str(uuid4()), "occurred_at": value},
            ).status_code
            == 422
        )
    cancelled = status(client, base, headers, original, "cancelled")
    assert cancelled.status_code == 200
    assert cancelled.json()["cancellation_reason"]
    assert (
        client.post(
            url + "/addenda",
            headers=headers,
            json={
                "request_id": str(uuid4()),
                "reason": "Synthetic correction",
                "content": "test",
            },
        ).status_code
        == 409
    )
    assert status(client, base, headers, cancelled.json(), "draft").status_code == 409


def test_encounter_permissions_clinic_scope_and_concurrency(
    registry, headers, patient_data
):
    client, settings, p, base, data, original = setup_visit(
        registry, headers, patient_data
    )

    async def registrar():
        return Principal("synthetic-registrar", settings.dev_clinic_id, ("registrar",))

    client.app.dependency_overrides[authenticate] = registrar
    assert client.get(base, headers=headers).status_code == 200
    assert (
        client.post(
            base, headers=headers, json={**data, "request_id": str(uuid4())}
        ).status_code
        == 403
    )

    async def foreign():
        return Principal("synthetic-other", uuid4(), ("clinician",))

    client.app.dependency_overrides[authenticate] = foreign
    assert client.get(base, headers=headers).status_code == 404
    assert client.get(f"{base}/{original['id']}", headers=headers).status_code == 404
    assert (
        client.put(
            f"{base}/{original['id']}",
            headers={**headers, "If-Match": '"1"'},
            json=content(),
        ).status_code
        == 404
    )
    client.app.dependency_overrides.clear()

    def edit(_):
        with TestClient(client.app) as concurrent:
            return concurrent.put(
                f"{base}/{original['id']}",
                headers={**headers, "If-Match": '"1"'},
                json=content(),
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit, range(2))) == [200, 412]
    assert client.get(base, headers=headers).json()["total"] == 1


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 0, -1])
def test_measurement_rejects_nonfinite_or_nonpositive(value):
    with pytest.raises(ValidationError):
        Measurement(**{**content()["measurements"][0], "weight_kg": value})


def test_cairo_date_age_and_concurrent_start(registry, headers, patient_data):
    client, settings = registry
    p = client.post("/v1/patients", headers=headers, json=patient_data).json()
    base = f"/v1/patients/{p['patient_id']}/encounters"
    payload = {
        "request_id": str(uuid4()),
        "occurred_at": "2023-06-14T22:30:00Z",
        "reason": "Synthetic birth-day visit",
        "consent_context": "Synthetic context",
    }

    def start(_):
        with TestClient(client.app) as other:
            return other.post(base, headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(start, range(2)))
    assert all(r.status_code == 201 for r in results)
    assert results[0].json() == results[1].json()
    assert results[0].json()["birth_context"]["age_days"] == 0
    assert client.get(base, headers=headers).json()["total"] == 1
    assert client.get(base).status_code == 401
