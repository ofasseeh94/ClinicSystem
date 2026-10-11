import hashlib
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .errors import Problem


@contextmanager
def connect(settings):
    if not settings.database_url:
        raise Problem(503, "database_unconfigured", "Registry storage is not configured.")
    try:
        with psycopg.connect(
            settings.database_url, row_factory=dict_row, connect_timeout=5
        ) as conn:
            yield conn
    except psycopg.errors.UndefinedTable:
        raise Problem(503, "migration_required", "Registry migrations must be applied.") from None
    except psycopg.OperationalError:
        raise Problem(
            503, "storage_unavailable", "Registry storage is temporarily unavailable."
        ) from None


def apply_migrations(database_url: str, directory: Path):
    """Transactions and checksums preserve applied migration history."""
    with psycopg.connect(database_url) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(783413)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(name text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        for path in sorted(directory.glob("[0-9]*.sql")):
            content = path.read_text(encoding="utf-8")
            digest = hashlib.sha256(content.encode()).hexdigest()
            previous = conn.execute(
                "SELECT sha256 FROM schema_migrations WHERE name=%s", (path.name,)
            ).fetchone()
            if previous:
                if previous[0] != digest:
                    raise ValueError(f"Applied migration changed: {path.name}")
                continue
            conn.execute(content)
            conn.execute(
                "INSERT INTO schema_migrations(name,sha256) VALUES (%s,%s)", (path.name, digest)
            )
