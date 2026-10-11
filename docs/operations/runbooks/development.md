# Development runbook

Follow the root README for setup and checks. PostgreSQL binds only to loopback; its named volume persists across container restarts. Stopping with `docker compose -f infrastructure/compose.yaml down` preserves the volume. Do not remove volumes containing needed data. Production backup, restore, incident and deployment procedures must be written and tested before real-data use.

Prefer a local NTFS checkout when dependency extraction fails on the Drive-mounted workspace. Never sync generated `node_modules` or virtual environments.
