import base64
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from clinic_api.config import Settings
from clinic_api.database import apply_migrations
from clinic_api.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "synthetic-test-token-" + "x" * 40


@pytest.fixture(scope="session")
def database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL required for PostgreSQL integration tests")
    with psycopg.connect(url) as conn:
        name = conn.execute("SELECT current_database()").fetchone()[0]
        if not name.endswith("_test"):
            raise RuntimeError(
                "Integration tests require a database name ending in _test"
            )
    apply_migrations(url, ROOT / "db/migrations")
    return url


@pytest.fixture
def registry(database_url):
    settings = Settings(
        database_url=database_url,
        environment="test",
        dev_token=TOKEN,
        dev_clinic_id=uuid4(),
        document_key=base64.b64encode(os.urandom(32)).decode(),
        document_scan_mode="synthetic",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        yield client, settings


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {TOKEN}", "Idempotency-Key": str(uuid4())}


@pytest.fixture
def patient_data():
    return {
        "name_ar": "أحمد طفل تجريبي",
        "name_en": "Synthetic Ahmed",
        "dob": "2023-06-15",
        "dob_precision": "exact",
        "growth_reference_sex": "male",
        "guardian": {
            "name": "Synthetic Guardian",
            "phone_e164": "+201000000001",
            "relation": "mother",
        },
        "aliases": ["حمودي تجريبي"],
    }
