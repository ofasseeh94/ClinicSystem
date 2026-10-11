import json
from pathlib import Path

import yaml
from clinic_api.config import Settings
from clinic_api.main import create_app


def test_published_openapi_matches_application():
    root = Path(__file__).resolve().parents[2]
    actual = create_app(Settings(environment="test")).openapi()
    assert yaml.safe_load((root / "docs/api/openapi.yaml").read_text(encoding="utf-8")) == actual
    assert (
        json.loads((root / "packages/shared-contracts/openapi.json").read_text(encoding="utf-8"))
        == actual
    )
