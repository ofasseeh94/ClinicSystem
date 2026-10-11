# Synthetic development runbook

Follow the root README. Keep database storage, venvs and npm dependencies on local NTFS when
working from the Google Drive-mounted repository. `scripts/sync-local.ps1` copies only non-ignored
source files, preserving the local dependency directory and excluding `.env`.

## Database and migrations

Docker: `docker compose --env-file .env -f infrastructure/compose.yaml up -d`.
The named volume persists across container restarts. `down` preserves the volume; never use
volume deletion as a dependency-install fix. Match DATABASE_URL to the chosen credentials/port.
Apply migrations explicitly with `python scripts/migrate.py`; the API does not alter schema on startup.
`/health` checks only the process; `/ready` checks PostgreSQL and applied migration count.

This workstation has EDB's PostgreSQL 17.11 Windows binaries at `%LOCALAPPDATA%/ClinicSystem/runtime/pgsql`.
The cluster is at `runtime/pgdata`; PostgreSQL listens on loopback port 55432. Credentials and the database
remain local and are excluded from Git. The standard README uses Docker port 5432 for other installations.

To start this existing local cluster, use the full local `pg_ctl.exe` path with:
`-D <runtime/pgdata> -l <runtime/postgres.log> -o "-p 55432 -h 127.0.0.1" -w start`.
To stop it safely, use `pg_ctl.exe -D <runtime/pgdata> -m fast -w stop`. Never delete the cluster to restart it.
These binaries are a development fallback, not a production installation or backup solution.
Official download references: [PostgreSQL Windows](https://www.postgresql.org/download/windows/) and
[EDB binary archives](https://www.enterprisedb.com/download-postgresql-binaries).

## Windows servers

`./scripts/start-dev.ps1` loads the ignored local `.env`, applies migrations, checks ports, writes a random
local access key and launches API/web processes hidden. `./scripts/stop-dev.ps1` checks recorded PID/start
identity before stopping the process trees; it leaves PostgreSQL data intact. Start failures should be
checked through `runtime/api.err.log` and `runtime/web.err.log`, without sharing credentials or patient data.
Vite proxies `/api`; for production, configure a protected HTTPS reverse proxy instead of using Vite.

## Acceptance tests

Set TEST_DATABASE_URL to a database ending `_test`. Pytest creates isolated synthetic clinic scopes and
rejects patient-database names. It does not truncate databases. Browser acceptance requires running dev
servers and DEV_AUTH_TOKEN; it creates explicitly fictional records in the development registry.
No real patient data belongs in tests, screenshots, prompts, errors or external services.

## Release gates

Development tokens are forbidden in production settings. JWT validation requires fixed HTTPS issuer/JWKS,
expected audience and signed staff clinic/role claims. A live provider and managed login/MFA, revocation,
restricted DB role, TLS/at-rest encryption, monitoring, distributed limits, backup/restore and incident
procedures are still open. No real-data launch is authorized by these setup instructions.
