import base64
import hashlib
import io
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import psycopg
import pytest
from clinic_api.auth import Principal, authenticate
from clinic_api.config import Settings
from clinic_api.records import files, service
from PIL import Image
from pypdf import PdfWriter


def png():
    stream = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, format="PNG")
    return stream.getvalue()


def setup_patient(registry, headers, patient_data):
    client, settings = registry
    row = client.post("/v1/patients", headers=headers, json=patient_data)
    assert row.status_code == 201, row.text
    return (
        client,
        settings,
        row.json()["patient_id"],
        f"/v1/patients/{row.json()['patient_id']}",
    )


def create_doc(client, headers, base):
    data = {
        "request_id": str(uuid4()),
        "title": "Fictional lab attachment",
        "category": "lab",
        "captured_at": "2025-05-01T10:00:00Z",
        "source": "Synthetic source",
    }
    row = client.post(base + "/documents", headers=headers, json=data)
    assert row.status_code == 201, row.text
    return data, row.json()


def upload(client, headers, base, doc, content=None, mime="image/png"):
    return client.put(
        base + f"/documents/{doc['id']}/content",
        headers={**headers, "Content-Type": mime},
        content=png() if content is None else content,
    )


def test_document_encrypt_replay_ticket_and_withdraw(registry, headers, patient_data):
    client, settings, pid, base = setup_patient(registry, headers, patient_data)
    data, doc = create_doc(client, headers, base)
    assert doc["state"] == "pending_upload"
    url = base + f"/documents/{doc['id']}"
    assert client.post(url + "/ticket", headers=headers).status_code == 409
    saved = upload(client, headers, base, doc)
    assert saved.status_code == 200, saved.text
    doc = saved.json()
    assert doc["state"] == "synthetic_ready"
    assert doc["sha256"] == hashlib.sha256(png()).hexdigest()
    assert upload(client, headers, base, doc).json() == doc
    assert client.post(base + "/documents", headers=headers, json=data).json() == doc
    assert (
        client.post(
            base + "/documents",
            headers=headers,
            json={**data, "title": "Changed title"},
        ).status_code
        == 409
    )
    with psycopg.connect(settings.database_url) as conn:
        encrypted = bytes(
            conn.execute(
                "SELECT encrypted_content FROM documents WHERE id=%s", (doc["id"],)
            ).fetchone()[0]
        )
        assert encrypted != png() and b"PNG" not in encrypted
    ticket = client.post(url + "/ticket", headers=headers).json()["ticket"]
    response = client.post(url + "/download", headers=headers, json={"ticket": ticket})
    assert response.status_code == 200 and response.content == png()
    assert (
        response.headers["Cache-Control"] == "no-store"
        and response.headers["X-Content-Type-Options"] == "nosniff"
    )
    claims = jwt.decode(
        ticket,
        service.ticket_key(settings),
        algorithms=["HS256"],
        audience="clinic-document-download",
    )
    claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired = jwt.encode(claims, service.ticket_key(settings), algorithm="HS256")
    assert (
        client.post(
            url + "/download", headers=headers, json={"ticket": expired}
        ).status_code
        == 403
    )
    _, other = create_doc(client, headers, base)
    assert (
        client.post(
            base + f"/documents/{other['id']}/download",
            headers=headers,
            json={"ticket": ticket},
        ).status_code
        == 403
    )
    assert (
        client.post(
            url + "/withdraw",
            headers={**headers, "If-Match": '"1"'},
            json={"reason": "Wrong synthetic attachment"},
        ).status_code
        == 412
    )
    withdrawn = client.post(
        url + "/withdraw",
        headers={**headers, "If-Match": f'"{doc["version"]}"'},
        json={"reason": "Wrong synthetic attachment"},
    )
    assert withdrawn.status_code == 200
    assert (
        client.post(
            url + "/download", headers=headers, json={"ticket": ticket}
        ).status_code
        == 409
    )
    assert upload(client, headers, base, doc).status_code == 409
    assert (
        client.post(
            url + "/withdraw", headers=headers, json={"reason": "Synthetic reason"}
        ).status_code
        == 428
    )
    rows = client.get(base + "/documents", headers=headers).json()["items"]
    assert all("encrypted_content" not in d for d in rows)
    for statement in (
        "DELETE FROM documents WHERE id=%s",
        "UPDATE documents SET title=title WHERE id=%s",
    ):
        with psycopg.connect(settings.database_url) as conn:
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(statement, (doc["id"],))
            conn.rollback()


def test_quarantine_rescan_integrity_and_role_scope(
    registry, headers, patient_data, monkeypatch
):
    client, settings, pid, base = setup_patient(registry, headers, patient_data)
    client.app.state.settings = replace(settings, document_scan_mode="clamav")
    _, doc = create_doc(client, headers, base)
    result = upload(client, headers, base, doc)
    assert result.status_code == 200
    doc = result.json()
    assert doc["state"] == "quarantined"
    url = base + f"/documents/{doc['id']}"
    assert client.post(url + "/ticket", headers=headers).status_code == 409
    monkeypatch.setattr(files, "scan", lambda *_: ("ready", "ClamAV scan passed"))
    released = client.post(
        url + "/rescan",
        headers={**headers, "If-Match": f'"{doc["version"]}"'},
        json={"reason": "Retry synthetic scanner fixture"},
    )
    assert released.json()["state"] == "ready"
    ticket = client.post(url + "/ticket", headers=headers).json()["ticket"]
    client.app.state.settings = replace(
        settings, document_key=base64.b64encode(b"b" * 32).decode()
    )
    assert (
        client.post(
            url + "/download", headers=headers, json={"ticket": ticket}
        ).status_code
        == 403
    )
    fresh = client.post(url + "/ticket", headers=headers).json()["ticket"]
    assert (
        client.post(
            url + "/download", headers=headers, json={"ticket": fresh}
        ).status_code
        == 503
    )
    client.app.state.settings = settings

    async def foreign():
        return Principal("foreign", uuid4(), ("clinician",))

    client.app.dependency_overrides[authenticate] = foreign
    assert client.get(base + "/documents", headers=headers).status_code == 404
    assert upload(client, headers, base, doc).status_code == 404
    assert client.post(url + "/ticket", headers=headers).status_code == 404

    async def auditor():
        return Principal("audit", settings.dev_clinic_id, ("auditor",))

    client.app.dependency_overrides[authenticate] = auditor
    assert client.get(base + "/documents", headers=headers).status_code == 403
    client.app.dependency_overrides.clear()
    assert client.get(base + "/documents").status_code == 401


def test_file_format_active_pdf_size_and_immutable_content(
    registry, headers, patient_data
):
    client, settings, pid, base = setup_patient(registry, headers, patient_data)
    _, doc = create_doc(client, headers, base)
    assert upload(client, headers, base, doc, b"<html>fake</html>").status_code == 422
    assert upload(client, headers, base, doc, png(), "text/html").status_code == 415
    assert upload(client, headers, base, doc, b"").status_code == 413
    assert (
        upload(client, headers, base, doc, b"x" * (files.MAX_BYTES + 1)).status_code
        == 413
    )
    assert upload(client, headers, base, doc, png(), "image/jpeg").status_code == 422
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_js("alert('Synthetic test')")
    stream = io.BytesIO()
    writer.write(stream)
    assert (
        upload(
            client, headers, base, doc, stream.getvalue(), "application/pdf"
        ).status_code
        == 422
    )
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    stream = io.BytesIO()
    writer.write(stream)
    assert (
        upload(
            client, headers, base, doc, stream.getvalue(), "application/pdf"
        ).status_code
        == 200
    )
    assert upload(client, headers, base, doc, png()).status_code == 409


def test_investigation_orders_results_corrections_and_patient_links(
    registry, headers, patient_data
):
    client, settings, pid, base = setup_patient(registry, headers, patient_data)
    encounter = client.post(
        base + "/encounters",
        headers=headers,
        json={
            "request_id": str(uuid4()),
            "occurred_at": "2025-01-01T10:00:00Z",
            "reason": "Synthetic visit",
            "consent_context": "Synthetic consent",
        },
    ).json()
    order_data = {
        "request_id": str(uuid4()),
        "encounter_id": encounter["id"],
        "test_name": "Synthetic Test",
        "indication": "Fictional investigation",
        "priority": "routine",
    }
    order = client.post(
        base + "/investigation-orders", headers=headers, json=order_data
    )
    assert order.status_code == 201, order.text
    order = order.json()
    url = base + f"/investigation-orders/{order['id']}/status"
    assert (
        client.post(
            base + "/investigation-orders", headers=headers, json=order_data
        ).json()
        == order
    )
    assert (
        client.post(
            url,
            headers={**headers, "If-Match": '"1"'},
            json={"status": "completed", "reason": "Synthetic completion"},
        ).status_code
        == 422
    )
    progress = client.post(
        url,
        headers={**headers, "If-Match": '"1"'},
        json={"status": "in_progress", "reason": "Synthetic collection"},
    ).json()
    assert progress["version"] == 2
    assert (
        client.post(
            url,
            headers={**headers, "If-Match": '"1"'},
            json={"status": "cancelled", "reason": "Synthetic cancellation"},
        ).status_code
        == 412
    )
    result_data = {
        "request_id": str(uuid4()),
        "order_id": order["id"],
        "test_name": "Synthetic Test",
        "collected_at": "2025-01-01T12:00:00Z",
        "value": "Fictional finding",
        "source": "Synthetic report",
        "reason": "Transcribe fictional report",
    }
    result = client.post(
        base + "/investigation-results", headers=headers, json=result_data
    )
    assert result.status_code == 201, result.text
    result = result.json()
    correction = {
        **result_data,
        "request_id": str(uuid4()),
        "supersedes_id": result["id"],
        "value": "Corrected fictional finding",
        "reason": "Fix synthetic transcription",
    }
    changed = client.post(
        base + "/investigation-results", headers=headers, json=correction
    )
    assert changed.status_code == 201, changed.text
    assert (
        client.post(
            base + "/investigation-results", headers=headers, json=correction
        ).status_code
        == 201
    )
    assert (
        client.post(
            base + "/investigation-results",
            headers=headers,
            json={**correction, "request_id": str(uuid4())},
        ).status_code
        == 409
    )
    listed = client.get(base + "/investigations", headers=headers).json()
    old = next(r for r in listed["results"] if r["id"] == result["id"])
    assert old["corrected_by_id"] == changed.json()["id"]
    complete = client.post(
        url,
        headers={**headers, "If-Match": '"2"'},
        json={"status": "completed", "reason": "Synthetic results reviewed"},
    )
    assert complete.status_code == 200
    assert (
        client.post(
            url,
            headers={**headers, "If-Match": '"3"'},
            json={"status": "cancelled", "reason": "Synthetic cancellation"},
        ).status_code
        == 409
    )
    sibling = client.post(
        "/v1/patients",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={
            **patient_data,
            "name_en": "Synthetic sibling",
            "name_ar": "",
            "guardian": {**patient_data["guardian"], "phone_e164": "+201000000002"},
        },
    ).json()["patient_id"]
    other = f"/v1/patients/{sibling}"
    assert (
        client.post(
            other + "/investigation-orders",
            headers=headers,
            json={**order_data, "request_id": str(uuid4())},
        ).status_code
        == 404
    )
    assert (
        client.post(
            other + "/investigation-results",
            headers=headers,
            json={**result_data, "request_id": str(uuid4())},
        ).status_code
        == 404
    )
    with psycopg.connect(settings.database_url) as conn:
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute(
                "UPDATE investigation_results SET value=%s WHERE id=%s",
                ("Changed", result["id"]),
            )
        conn.rollback()

    async def registrar():
        return Principal("registrar", settings.dev_clinic_id, ("registrar",))

    client.app.dependency_overrides[authenticate] = registrar
    assert client.get(base + "/investigations", headers=headers).status_code == 200
    assert (
        client.post(
            base + "/investigation-orders",
            headers=headers,
            json={**order_data, "request_id": str(uuid4())},
        ).status_code
        == 403
    )


def test_synthetic_scan_production_guard_and_missing_key():
    with pytest.raises(ValueError):
        Settings(environment="production", document_scan_mode="synthetic")
    with pytest.raises(ValueError):
        Settings(document_key="invalid")
    secret_key = base64.b64encode(b"s" * 32).decode()
    assert secret_key not in repr(Settings(document_key=secret_key))
    from clinic_api.errors import Problem

    with pytest.raises(Problem):
        files.key(Settings())
    production = Settings(
        environment="production",
        database_url="postgresql://unused",
        oidc_issuer="https://issuer.example",
        oidc_jwks_url="https://issuer.example/jwks",
        oidc_audience="clinic",
        document_key=secret_key,
    )
    with pytest.raises(Problem):
        service.readable(production, {"state": "synthetic_ready"})
    with pytest.raises(ValueError):
        Settings(clamav_port=0)
