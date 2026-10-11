"""Patient registry application; authenticated, PostgreSQL-backed, synthetic development only."""

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

import jwt
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from .config import Settings
from .database import connect
from .encounters.routes import router as encounters_router
from .errors import Problem, problem_response
from .registry.routes import router


class HealthResponse(BaseModel):
    status: str = "ok"


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="Pediatric Clinic API", version="0.1.0")
    app.state.settings = settings
    app.state.jwks = (
        jwt.PyJWKClient(settings.oidc_jwks_url, cache_keys=True) if settings.oidc_jwks_url else None
    )
    buckets = defaultdict(deque)
    bucket_lock = Lock()

    @app.middleware("http")
    async def request_controls(request: Request, call_next):
        request.state.request_id = str(uuid4())
        # Single-process baseline limit, keyed by network peer; distributed limiter remains a release gate.
        peer = request.client.host if request.client else "unknown"
        now = time.monotonic()
        limited = False
        with bucket_lock:
            bucket = buckets[peer]
            while bucket and bucket[0] < now - 60:
                bucket.popleft()
            if len(bucket) >= 240:
                limited = True
            else:
                bucket.append(now)
            # Bound idle peer retention; do not trust client-supplied forwarding headers.
            if len(buckets) > 10000:
                for key in list(buckets):
                    if not buckets[key] or buckets[key][-1] < now - 60:
                        del buckets[key]
        if limited:
            response = problem_response(
                request, Problem(429, "rate_limited", "Too many requests. Try again shortly.")
            )
            response.headers["Retry-After"] = "60"
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(Problem)
    async def domain_error(request, exc):
        return problem_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Never echo supplied names, phones, credentials or validation input values.
        safe_parts = {
            "body",
            "query",
            "path",
            "header",
            "name_ar",
            "name_en",
            "dob",
            "dob_precision",
            "dob_source",
            "growth_reference_sex",
            "guardian",
            "name",
            "phone_e164",
            "relation",
            "aliases",
            "allergy_review_status",
            "allergies",
            "substance",
            "reaction",
            "background",
            "form_key",
            "version",
            "answers",
            "audit_reason",
            "duplicate_review_reason",
            "page",
            "page_size",
            "patient_id",
            "idempotency-key",
            "if-match",
            "entity_id",
            "after",
            "limit",
            "key",
        }
        fields = [
            ".".join(str(p) for p in e["loc"] if isinstance(p, int) or p in safe_parts)
            for e in exc.errors()
        ]
        return problem_response(
            request,
            Problem(422, "invalid_request", "Check the highlighted request fields.", fields=fields),
        )

    @app.get("/health", response_model=HealthResponse, operation_id="health")
    def health():
        """Process health only; does not check dependencies."""
        return HealthResponse()

    @app.get("/ready", response_model=HealthResponse)
    def ready():
        with connect(settings) as conn:
            try:
                from psycopg.errors import UndefinedTable

                count = conn.execute("SELECT count(*) AS n FROM schema_migrations").fetchone()["n"]
                if count < 3:
                    raise Problem(503, "migration_required", "Registry migrations must be applied.")
            except UndefinedTable:
                raise Problem(
                    503, "migration_required", "Registry migrations must be applied."
                ) from None
        return HealthResponse()

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return problem_response(
            request,
            Problem(exc.status_code, "http_error", "The requested resource is unavailable."),
        )

    app.include_router(router)
    app.include_router(encounters_router)
    default_openapi = app.openapi

    def documented_schema():
        schema = default_openapi()
        for path in schema["paths"].values():
            for operation in path.values():
                for code, response in operation.get("responses", {}).items():
                    content = response.get("content", {})
                    if code.isdigit() and int(code) >= 400 and "application/json" in content:
                        content["application/problem+json"] = content.pop("application/json")
        return schema

    app.openapi = documented_schema
    return app


app = create_app()
