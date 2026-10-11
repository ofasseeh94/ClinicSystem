import re
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from ..auth import Principal, authenticate
from ..database import connect
from ..errors import Problem
from . import audit, forms, service
from . import repository as repo
from .schemas import (
    AuditResponse,
    FormSubmission,
    PatientCreate,
    PatientRecord,
    PatientUpdate,
    ProblemResponse,
    PublishedForm,
    SearchRequest,
    SearchResponse,
    SessionResponse,
)

router = APIRouter(
    prefix="/v1",
    tags=["Registry"],
    responses={
        status: {
            "model": ProblemResponse,
            "description": "Problem response; supplied values are never echoed",
        }
        for status in (400, 401, 403, 404, 409, 412, 422, 428, 429, 503)
    },
)


def expected_version(value):
    if value is None:
        raise Problem(
            428, "precondition_required", "Provide the current record ETag with If-Match."
        )
    if not re.fullmatch(r'"[1-9][0-9]*"', value):
        raise Problem(400, "invalid_etag", "If-Match must contain a quoted record version.")
    return int(value[1:-1])


@router.get("/session", response_model=SessionResponse)
def session(request: Request, principal: Principal = Depends(authenticate)):
    return {
        "actor_id": principal.actor_id,
        "clinic_id": principal.clinic_id,
        "roles": list(principal.roles),
        "environment": request.app.state.settings.environment,
    }


@router.post("/patients/search", response_model=SearchResponse)
def search(data: SearchRequest, request: Request, principal: Principal = Depends(authenticate)):
    principal.require("patient:read")
    with connect(request.app.state.settings) as conn:
        result = repo.search(conn, principal.clinic_id, data)
        # Audit access IDs only; never put the search text in logs or audit payloads.
        audit.append(
            conn,
            principal,
            "patient.search",
            after={"returned_ids": [str(p["patient_id"]) for p in result["items"]]},
        )
        return result


@router.post("/patients", status_code=201, response_model=PatientRecord)
def create(
    data: PatientCreate,
    request: Request,
    response: Response,
    idempotency_key: UUID = Header(),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        result = service.create(conn, principal, data, idempotency_key)
        response.headers["ETag"] = f'"{result["version"]}"'
        response.headers["Location"] = f"/v1/patients/{result['patient_id']}"
        return result


@router.get("/patients/{patient_id}", response_model=PatientRecord)
def read(
    patient_id: UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(authenticate),
):
    principal.require("patient:read")
    with connect(request.app.state.settings) as conn:
        result = repo.patient(conn, principal.clinic_id, patient_id)
        audit.append(conn, principal, "patient.read", patient_id)
        response.headers["ETag"] = f'"{result["version"]}"'
        return result


@router.patch("/patients/{patient_id}", response_model=PatientRecord)
def update(
    patient_id: UUID,
    data: PatientUpdate,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    version = expected_version(if_match)
    with connect(request.app.state.settings) as conn:
        result = service.update(conn, principal, patient_id, data, version)
        response.headers["ETag"] = f'"{result["version"]}"'
        return result


@router.get("/forms/{key}/versions/{version}", response_model=PublishedForm)
def form_schema(
    key: str, version: int, request: Request, principal: Principal = Depends(authenticate)
):
    principal.require("form:read")
    with connect(request.app.state.settings) as conn:
        return forms.definition(conn, key, version)


@router.post("/patients/{patient_id}/form-responses", status_code=201, response_model=PatientRecord)
def submit_form(
    patient_id: UUID,
    data: FormSubmission,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        result = service.submit_form(conn, principal, patient_id, data, expected_version(if_match))
        response.headers["ETag"] = f'"{result["version"]}"'
        return result


@router.get("/audit", response_model=AuditResponse)
def read_audit(
    request: Request,
    entity_id: UUID | None = None,
    after: int = 0,
    limit: int = 50,
    principal: Principal = Depends(authenticate),
):
    principal.require("audit:read")
    if after < 0 or limit < 1 or limit > 100:
        raise Problem(
            422,
            "invalid_pagination",
            "Audit page size must be 1–100 and cursor must be nonnegative.",
        )
    with connect(request.app.state.settings) as conn:
        audit.append(conn, principal, "audit.read", entity_id)
        rows = conn.execute(
            "SELECT sequence,id,payload,event_hash,previous_hash,created_at FROM audit_events "
            "WHERE clinic_id=%s AND sequence>%s AND (%s::uuid IS NULL OR record_id=%s) "
            "ORDER BY sequence LIMIT %s",
            (principal.clinic_id, after, entity_id, entity_id, limit),
        ).fetchall()
        return {"items": rows, "next_cursor": rows[-1]["sequence"] if rows else after}
