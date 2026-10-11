"""Run ordered PostgreSQL migrations; no automatic destructive rollback."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from clinic_api.database import apply_migrations  # noqa: E402

if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL before running migrations")
    apply_migrations(url, ROOT / "db/migrations")
    print("PostgreSQL migrations applied and checksums verified.")
