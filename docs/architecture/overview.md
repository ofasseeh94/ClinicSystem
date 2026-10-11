# Architecture

Target: React/TypeScript browser → managed authentication → FastAPI → PostgreSQL.
Private document storage, deterministic clinical rules, task queue and AI gateway are future components.

Current implementation consists of a foundation web page and a health-only API.
The browser has no database credentials. No patient data, identity provider, storage or clinical engine exists yet.
Single-clinic deployment is intended, with explicit clinic scoping required before registry implementation.
Hosting region and managed identity provider remain undecided. No production deployment is configured.
