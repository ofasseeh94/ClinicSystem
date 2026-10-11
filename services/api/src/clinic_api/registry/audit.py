"""Atomic, clinic-scoped hash-chained access/change evidence."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from psycopg.types.json import Jsonb


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def lock_clinic(conn, clinic_id):
    # PostgreSQL transaction lock serializes registration, revisions and audit-chain appends.
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(clinic_id),))


def append(conn, principal, action, record_id=None, before=None, after=None, reason=None):
    lock_clinic(conn, principal.clinic_id)
    last = conn.execute(
        "SELECT event_hash FROM audit_events WHERE clinic_id=%s ORDER BY sequence DESC LIMIT 1",
        (principal.clinic_id,),
    ).fetchone()
    previous = last["event_hash"] if last else "0" * 64
    event = {
        "id": str(uuid4()),
        "clinic_id": str(principal.clinic_id),
        "actor": principal.actor_id,
        "action": action,
        "record_id": str(record_id) if record_id else None,
        "before": before,
        "after": after,
        "reason": reason,
        "time": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous,
    }
    digest = hashlib.sha256(canonical(event).encode()).hexdigest()
    conn.execute(
        "INSERT INTO audit_events(id,clinic_id,actor,action,record_id,payload,previous_hash,event_hash) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            event["id"],
            principal.clinic_id,
            principal.actor_id,
            action,
            record_id,
            Jsonb(json.loads(canonical(event))),
            previous,
            digest,
        ),
    )
