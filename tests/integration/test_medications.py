from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest
from clinic_api.auth import Principal, authenticate


def catalog_data():
    return {
        "request_id": str(uuid4()),
        "product_name": "Fictional Product A",
        "generic_name": "Fictional ingredient",
        "formulation": "Not a clinical formulation",
        "strength_text": "Not a clinical strength",
        "route_text": "Not for administration",
        "source_kind": "synthetic",
        "source_title": "Fictional reference",
        "source_publisher": "Fixture publisher",
        "source_version": "Fixture v1",
        "source_url": "",
        "source_country": "Synthetic",
        "source_checked_on": "2025-01-01",
    }


def patient(client, headers, data):
    response = client.post("/v1/patients", headers=headers, json=data)
    assert response.status_code == 201, response.text
    return response.json()["patient_id"]


def review(client, headers, c, state):
    return client.post(
        f"/v1/medication-catalog/versions/{c['id']}/status",
        headers={**headers, "If-Match": f'"{c["revision"]}"'},
        json={"state": state, "reason": "Fixture independent source review"},
    )


def test_catalog_versions_replay_review_and_immutable_content(registry, headers):
    client, settings = registry
    data = catalog_data()
    created = client.post("/v1/medication-catalog", headers=headers, json=data)
    assert created.status_code == 201, created.text
    c = created.json()
    assert c["version"] == 1 and c["state"] == "draft"
    assert client.post("/v1/medication-catalog", headers=headers, json=data).json() == c
    assert (
        client.post(
            "/v1/medication-catalog",
            headers=headers,
            json={**data, "product_name": "Different"},
        ).status_code
        == 409
    )
    submitted = review(client, headers, c, "in_review")
    assert submitted.status_code == 200
    c = submitted.json()
    assert c["revision"] == 2
    assert review(client, headers, c, "verified_identity").status_code == 403
    assert (
        client.post(
            f"/v1/medication-catalog/versions/{c['id']}/status",
            headers={**headers, "If-Match": '"1"'},
            json={"state": "retired", "reason": "Fixture retirement"},
        ).status_code
        == 412
    )
    assert (
        client.post(
            f"/v1/medication-catalog/versions/{c['id']}/status",
            headers=headers,
            json={"state": "retired", "reason": "Fixture retirement"},
        ).status_code
        == 428
    )
    updated = client.post(
        f"/v1/medication-catalog/{c['catalog_id']}/versions",
        headers=headers,
        json={**data, "request_id": str(uuid4()), "source_version": "Fixture v2"},
    )
    assert updated.status_code == 201, updated.text
    assert updated.json()["version"] == 2
    assert client.get("/v1/medication-catalog", headers=headers).json()["total"] == 2
    for sql in (
        "UPDATE medication_catalog SET product_name=%s WHERE id=%s",
        "DELETE FROM medication_catalog WHERE product_name=%s AND id=%s",
    ):
        with psycopg.connect(settings.database_url) as conn:
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(sql, ("Fictional Product A", c["id"]))
            conn.rollback()


def test_independent_identity_verification_does_not_enable_clinical_engine(
    registry, headers, patient_data
):
    client, settings = registry
    data = {
        **catalog_data(),
        "source_kind": "regulatory_label",
        "source_url": "https://regulator.example/fixture",
        "source_title": "Simulated source for protocol testing",
    }
    c = client.post("/v1/medication-catalog", headers=headers, json=data).json()
    c = review(client, headers, c, "in_review").json()

    async def self_reviewer():
        return Principal(
            "synthetic-development-staff",
            settings.dev_clinic_id,
            ("clinical_reviewer",),
        )

    client.app.dependency_overrides[authenticate] = self_reviewer
    assert review(client, headers, c, "verified_identity").status_code == 409

    async def independent():
        return Principal(
            "fixture-independent-reviewer",
            settings.dev_clinic_id,
            ("clinical_reviewer", "clinician"),
        )

    client.app.dependency_overrides[authenticate] = independent
    reviewed = review(client, headers, c, "verified_identity")
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewed_by"] == "fixture-independent-reviewer"
    caps = client.get("/v1/medication-capabilities", headers=headers).json()
    assert not caps["dose_calculation_enabled"] and not caps["prescribing_enabled"]
    pid = patient(client, headers, patient_data)
    for action in ("calculate", "prescribe"):
        blocked = client.post(
            f"/v1/patients/{pid}/medications/{action}",
            headers=headers,
            json={"unsafe_input": "should never be processed"},
        )
        assert blocked.status_code == 409 and "unsafe_input" not in blocked.text
    assert (
        client.get(f"/v1/patients/{pid}/medications", headers=headers).json()["total"]
        == 0
    )
    client.app.dependency_overrides.clear()
    events = client.get("/v1/audit", headers=headers, params={"entity_id": pid}).json()[
        "items"
    ]
    assert {"medication.blocked_calculation", "medication.blocked_prescribing"} <= {
        e["payload"]["action"] for e in events
    }


def test_synthetic_source_and_development_identity_approval_are_blocked(
    registry, headers
):
    client, settings = registry
    c = client.post(
        "/v1/medication-catalog", headers=headers, json=catalog_data()
    ).json()
    c = review(client, headers, c, "in_review").json()

    async def independent():
        return Principal(
            "fixture-reviewer", settings.dev_clinic_id, ("clinical_reviewer",)
        )

    client.app.dependency_overrides[authenticate] = independent
    assert review(client, headers, c, "verified_identity").status_code == 409
    real = {
        **catalog_data(),
        "request_id": str(uuid4()),
        "source_kind": "formulary",
        "source_url": "https://reference.example/fixture",
    }
    c = client.post("/v1/medication-catalog", headers=headers, json=real).json()
    c = review(client, headers, c, "in_review").json()
    client.app.state.settings = replace(settings, environment="development")
    assert review(client, headers, c, "verified_identity").status_code == 409


def test_reported_history_corrections_scope_and_retention(
    registry, headers, patient_data
):
    client, settings = registry
    pid = patient(client, headers, patient_data)
    base = f"/v1/patients/{pid}/medications"
    data = {
        "request_id": str(uuid4()),
        "medication_name": "Fictional reported product",
        "reported_instructions": "Dose not known; fictional history only",
        "use_status": "unknown",
        "recorded_for": "2025-01-01T10:00:00Z",
        "source": "Fictional guardian report",
        "reason": "Record fixture history",
    }
    response = client.post(base, headers=headers, json=data)
    assert response.status_code == 201, response.text
    row = response.json()
    assert client.post(base, headers=headers, json=data).json() == row
    correction = {
        **data,
        "request_id": str(uuid4()),
        "supersedes_id": row["id"],
        "use_status": "stopped",
        "reason": "Clarify fixture reported use",
    }
    changed = client.post(base, headers=headers, json=correction)
    assert changed.status_code == 201
    assert (
        client.post(
            base, headers=headers, json={**correction, "request_id": str(uuid4())}
        ).status_code
        == 409
    )
    old = next(
        r
        for r in client.get(base, headers=headers).json()["items"]
        if r["id"] == row["id"]
    )
    assert (
        old["use_status"] == "unknown"
        and old["corrected_by_id"] == changed.json()["id"]
    )
    draft = client.post(
        "/v1/medication-catalog", headers=headers, json=catalog_data()
    ).json()
    assert (
        client.post(
            base,
            headers=headers,
            json={
                **data,
                "request_id": str(uuid4()),
                "catalog_version_id": draft["id"],
            },
        ).status_code
        == 409
    )
    with psycopg.connect(settings.database_url) as conn:
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute(
                "UPDATE medication_statements SET source=source WHERE id=%s",
                (row["id"],),
            )
        conn.rollback()

    async def other():
        return Principal("fixture-other", uuid4(), ("clinician",))

    client.app.dependency_overrides[authenticate] = other
    assert client.get(base, headers=headers).status_code == 404
    assert client.get("/v1/medication-catalog", headers=headers).json()["total"] == 0
    assert (
        client.post(
            f"/v1/medication-catalog/versions/{draft['id']}/status",
            headers={**headers, "If-Match": '"1"'},
            json={"state": "in_review", "reason": "Fixture review"},
        ).status_code
        == 404
    )

    async def registrar():
        return Principal("fixture-registrar", settings.dev_clinic_id, ("registrar",))

    client.app.dependency_overrides[authenticate] = registrar
    assert client.get(base, headers=headers).status_code == 200
    assert (
        client.post(
            base, headers=headers, json={**data, "request_id": str(uuid4())}
        ).status_code
        == 403
    )
    client.app.dependency_overrides.clear()
    assert client.get(base).status_code == 401


@pytest.mark.parametrize(
    "url",
    [
        "http://reference.example",
        "javascript:alert(1)",
        "https://user:password@reference.example",
    ],
)
def test_source_url_validation(registry, headers, url):
    client, _ = registry
    assert (
        client.post(
            "/v1/medication-catalog",
            headers=headers,
            json={**catalog_data(), "source_url": url},
        ).status_code
        == 422
    )
