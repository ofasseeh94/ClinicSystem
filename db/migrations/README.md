# PostgreSQL migrations

001_registry.sql creates the normalized registry, audit chain and immutable form history.
002_background_v2.sql adds background v2 without modifying v1.

Run `python scripts/migrate.py` with DATABASE_URL set. Scripts execute in order inside a transaction,
with an advisory migration lock and persisted SHA-256 checksums. Repeated application is idempotent;
changed applied files are rejected. There is no SQLite fallback or automatic migration during API startup.

No destructive down migration is offered: destroying registry history is not a safe rollback.
Before schema changes take a PostgreSQL backup, test restoration and introduce a new migration.
Synthetic test data can use a new isolated *_test database; never reset a patient database for tests.
