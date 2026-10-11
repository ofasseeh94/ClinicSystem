import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from clinic_api.config import Settings  # noqa: E402
from clinic_api.main import create_app  # noqa: E402

schema = create_app(Settings(environment="test")).openapi()
(ROOT / "docs/api/openapi.yaml").write_text(
    yaml.safe_dump(schema, sort_keys=False, allow_unicode=True), encoding="utf-8"
)
(ROOT / "packages/shared-contracts/openapi.json").write_text(
    json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
print("OpenAPI YAML and shared JSON contracts generated.")
