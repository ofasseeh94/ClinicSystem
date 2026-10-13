from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request

from ..auth import Principal, authenticate
from ..database import connect
from ..errors import Problem
from ..records.service import scope
from ..registry import audit
from ..registry.routes import expected_version
from ..registry.schemas import ProblemResponse
from . import service
from .schemas import (
    Capabilities,
    CatalogInput,
    CatalogPage,
    CatalogRecord,
    CatalogTransition,
    StatementInput,
    StatementPage,
    StatementRecord,
)

router = APIRouter(
    prefix="/v1",
    tags=["Medication foundation"],
    responses={
        s: {
            "model": ProblemResponse,
            "description": "Problem response; supplied values are never echoed",
        }
        for s in (400, 401, 403, 404, 409, 412, 422, 428, 503)
    },
)


@router.get("/medication-capabilities", response_model=Capabilities)
def capabilities(principal: Principal = Depends(authenticate)):
    principal.require("medication:read")
    return Capabilities()


@router.get("/medication-catalog", response_model=CatalogPage)
def catalog_list(
    request: Request,
    page: int = Query(default=1, ge=1, le=1000000),
    principal: Principal = Depends(authenticate),
):
    principal.require("medication:read")
    with connect(request.app.state.settings) as conn:
        rows = conn.execute(
            "SELECT * FROM medication_catalog WHERE clinic_id=%s ORDER BY created_at DESC,id LIMIT 20 OFFSET %s",
            (principal.clinic_id, (page - 1) * 20),
        ).fetchall()
        count = conn.execute(
            "SELECT count(*) AS n FROM medication_catalog WHERE clinic_id=%s",
            (principal.clinic_id,),
        ).fetchone()["n"]
        audit.append(
            conn,
            principal,
            "medication.catalog_read",
            after={"returned_ids": [str(r["id"]) for r in rows]},
        )
        return {
            "items": [service.public(r, CatalogRecord) for r in rows],
            "total": count,
            "page": page,
        }


@router.post("/medication-catalog", response_model=CatalogRecord, status_code=201)
def create_catalog(
    data: CatalogInput, request: Request, principal: Principal = Depends(authenticate)
):
    with connect(request.app.state.settings) as conn:
        return service.create_catalog(conn, request.app.state.settings, principal, data)


@router.post(
    "/medication-catalog/{catalog_id}/versions", response_model=CatalogRecord, status_code=201
)
def version(
    catalog_id: UUID,
    data: CatalogInput,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.create_catalog(conn, request.app.state.settings, principal, data, catalog_id)


@router.post("/medication-catalog/versions/{version_id}/status", response_model=CatalogRecord)
def review(
    version_id: UUID,
    data: CatalogTransition,
    request: Request,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.transition(
            conn,
            request.app.state.settings,
            principal,
            version_id,
            expected_version(if_match),
            data,
        )


@router.get("/patients/{patient_id}/medications", response_model=StatementPage)
def history(
    patient_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1, le=1000000),
    principal: Principal = Depends(authenticate),
):
    principal.require("medication:read")
    with connect(request.app.state.settings) as conn:
        scope(conn, principal, patient_id)
        rows = conn.execute(
            "SELECT s.*,c.id AS corrected_by_id FROM medication_statements s LEFT JOIN medication_statements c ON c.clinic_id=s.clinic_id AND c.supersedes_id=s.id WHERE s.clinic_id=%s AND s.patient_id=%s ORDER BY s.recorded_for DESC,s.created_at DESC,s.id LIMIT 20 OFFSET %s",
            (principal.clinic_id, patient_id, (page - 1) * 20),
        ).fetchall()
        count = conn.execute(
            "SELECT count(*) AS n FROM medication_statements WHERE clinic_id=%s AND patient_id=%s",
            (principal.clinic_id, patient_id),
        ).fetchone()["n"]
        audit.append(
            conn,
            principal,
            "medication.history_read",
            patient_id,
            after={"returned_ids": [str(r["id"]) for r in rows]},
        )
        return {
            "items": [service.public(r, StatementRecord) for r in rows],
            "total": count,
            "page": page,
        }


@router.post("/patients/{patient_id}/medications", response_model=StatementRecord, status_code=201)
def record_history(
    patient_id: UUID,
    data: StatementInput,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.create_statement(conn, principal, patient_id, data)


def blocked(request, principal, patient_id, action):
    principal.require("medication:history_write")
    with connect(request.app.state.settings) as conn:
        scope(conn, principal, patient_id)
        audit.append(
            conn,
            principal,
            "medication.blocked_" + action,
            patient_id,
            after={"clinical_engine_enabled": False},
        )
    raise Problem(
        409,
        "clinical_engine_unavailable",
        "Dose calculation and prescribing are disabled until approved sources, independently verified clinical rules and release review are established.",
    )


@router.post("/patients/{patient_id}/medications/calculate", response_model=ProblemResponse)
def calculate(patient_id: UUID, request: Request, principal: Principal = Depends(authenticate)):
    return blocked(request, principal, patient_id, "calculation")


@router.post("/patients/{patient_id}/medications/prescribe", response_model=ProblemResponse)
def prescribe(patient_id: UUID, request: Request, principal: Principal = Depends(authenticate)):
    return blocked(request, principal, patient_id, "prescribing")
