# ADR-001: Initial application stack

Status: Accepted for scaffold; production hosting and identity remain open
Date: 2026-10-10
Owner: Project maintainer

Decision: React + TypeScript + Vite frontend, Python FastAPI backend and PostgreSQL.
The user requested repository establishment before individual features. These defaults follow the
engineering specification and can be revisited before M1 via a superseding ADR.

Alternatives: NestJS offers one-language development; FastAPI offers typed request validation
and a Python ecosystem suitable for future deterministic clinical calculations.

Security and clinical impact: no authentication bypass, prescribing rules or real-data handling is
introduced. Managed identity, clinic authorization and audited transactions are prerequisites for M1.

Compatibility and recovery: no applied migrations or persisted application data exist.
Validate with scaffold, web build and health tests. Stack reversal currently requires only scaffold changes.
