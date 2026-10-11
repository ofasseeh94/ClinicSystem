from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from clinic_api.auth import Principal, authenticate
from clinic_api.config import Settings
from clinic_api.main import create_app
from conftest import TOKEN
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient


def test_authentication_and_error_redaction(registry, headers, patient_data):
    client, _ = registry
    for h in ({}, {"Authorization": "Bearer wrong"}):
        assert (
            client.post("/v1/patients/search", headers=h, json={"query": "Synthetic"}).status_code
            == 401
        )
    result = client.post(
        "/v1/patients",
        headers=headers,
        json={
            **patient_data,
            "guardian": {"name": "Private test", "phone_e164": "private-test-phone"},
        },
    )
    assert result.status_code == 422
    assert "private-test-phone" not in result.text and "Private test" not in result.text
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Request-ID"]
    assert result.headers["content-type"].startswith("application/problem+json")


def test_clinic_isolation(registry, headers, patient_data):
    client, settings = registry
    row = client.post("/v1/patients", headers=headers, json=patient_data).json()
    other = create_app(
        Settings(
            database_url=settings.database_url,
            environment="test",
            dev_token=TOKEN,
            dev_clinic_id=uuid4(),
        )
    )
    with TestClient(other) as second:
        path = f"/v1/patients/{row['patient_id']}"
        assert second.get(path, headers=headers).status_code == 404
        assert (
            second.patch(
                path,
                headers={**headers, "If-Match": '"1"'},
                json={**patient_data, "audit_reason": "Cross clinic attempt"},
            ).status_code
            == 404
        )
        assert (
            second.post("/v1/patients/search", headers=headers, json={"query": ""}).json()["total"]
            == 0
        )
        items = second.get(
            "/v1/audit", headers=headers, params={"entity_id": row["patient_id"]}
        ).json()["items"]
        assert all(e["payload"]["action"] == "audit.read" for e in items)


def test_role_enforcement(registry, headers, patient_data):
    client, settings = registry
    client.app.dependency_overrides[authenticate] = lambda: Principal(
        "synthetic-auditor", settings.dev_clinic_id, ("auditor",)
    )
    assert client.post("/v1/patients", headers=headers, json=patient_data).status_code == 403
    assert (
        client.post("/v1/patients/search", headers=headers, json={"query": ""}).status_code == 403
    )
    client.app.dependency_overrides[authenticate] = lambda: Principal(
        "synthetic-registrar", settings.dev_clinic_id, ("registrar",)
    )
    assert client.get("/v1/audit", headers=headers).status_code == 403


def test_production_rejects_development_auth_and_validates_jwt():
    with pytest.raises(ValueError, match="forbidden"):
        Settings(environment="production", dev_token=TOKEN)
    with pytest.raises(ValueError):
        Settings(environment="production")
    settings = Settings(
        environment="production",
        database_url="postgresql://unused",
        oidc_issuer="https://identity.example.test/",
        oidc_audience="clinic",
        oidc_jwks_url="https://identity.example.test/jwks",
    )
    app = create_app(settings)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    app.state.jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda _: SimpleNamespace(key=key.public_key())
    )
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "synthetic-staff",
        "iss": settings.oidc_issuer,
        "aud": "clinic",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "clinic_id": str(uuid4()),
        "roles": ["registrar"],
    }
    with TestClient(app) as client:

        def call(payload, algorithm="RS256"):
            encoded = jwt.encode(
                payload,
                key if algorithm == "RS256" else "wrong-key-" + "x" * 40,
                algorithm=algorithm,
            )
            return client.get("/v1/session", headers={"Authorization": f"Bearer {encoded}"})

        assert call(claims).status_code == 200
        assert call({**claims, "aud": "other"}).status_code == 401
        assert call({**claims, "exp": now - timedelta(seconds=1)}).status_code == 401
        assert call({**claims, "clinic_id": "bad"}).status_code == 401
        assert call(claims, "HS256").status_code == 401
        assert (
            client.get("/v1/session", headers={"Authorization": f"Bearer {TOKEN}"}).status_code
            == 401
        )


def test_precondition_and_literal_search(registry, headers, patient_data):
    client, _ = registry
    row = client.post("/v1/patients", headers=headers, json=patient_data).json()
    result = client.patch(
        f"/v1/patients/{row['patient_id']}",
        headers=headers,
        json={**patient_data, "audit_reason": "Test missing precondition"},
    )
    assert result.status_code == 428
    for query in ("%", "_", "' OR 1=1 --"):
        result = client.post("/v1/patients/search", headers=headers, json={"query": query})
        assert result.status_code == 200 and result.json()["total"] == 0


def test_configuration_repr_hides_credentials():
    settings = Settings(
        database_url="postgresql://staff:private-password@localhost/clinic_test", dev_token=TOKEN
    )
    assert "private-password" not in repr(settings)
    assert TOKEN not in repr(settings)
