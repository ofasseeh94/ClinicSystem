from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from ..auth import Principal, authenticate
from ..database import connect
from ..registry import audit
from ..registry.routes import expected_version
from ..registry.schemas import ProblemResponse
from . import service
from .schemas import (
    AddendumCreate,
    EncounterCreate,
    EncounterPage,
    EncounterRecord,
    EncounterUpdate,
    Transition,
)

router = APIRouter(
    prefix="/v1/patients/{patient_id}/encounters",
    tags=["Encounters"],
    responses={
        s: {"model": ProblemResponse} for s in (400, 401, 403, 404, 409, 412, 422, 428, 503)
    },
)


def tagged(response, result):
    response.headers["ETag"] = f'"{result["version"]}"'
    return result


@router.post("", status_code=201, response_model=EncounterRecord)
def create(
    patient_id: UUID,
    data: EncounterCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return tagged(response, service.create(conn, principal, patient_id, data))


@router.get("", response_model=EncounterPage)
def timeline(
    patient_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    principal: Principal = Depends(authenticate),
):
    principal.require("encounter:read")
    with connect(request.app.state.settings) as conn:
        service.patient(conn, principal, patient_id)
        total = conn.execute(
            "SELECT count(*) AS n FROM encounters WHERE clinic_id=%s AND patient_id=%s",
            (principal.clinic_id, patient_id),
        ).fetchone()["n"]
        rows = conn.execute(
            "SELECT id FROM encounters WHERE clinic_id=%s AND patient_id=%s "
            "ORDER BY occurred_at DESC,id LIMIT 20 OFFSET %s",
            (principal.clinic_id, patient_id, (page - 1) * 20),
        ).fetchall()
        audit.append(
            conn,
            principal,
            "encounter.timeline",
            patient_id,
            after={"returned_ids": [str(r["id"]) for r in rows]},
        )
        return {
            "items": [service.read(conn, principal, patient_id, r["id"]) for r in rows],
            "total": total,
            "page": page,
        }


@router.get("/{encounter_id}", response_model=EncounterRecord)
def read(
    patient_id: UUID,
    encounter_id: UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(authenticate),
):
    principal.require("encounter:read")
    with connect(request.app.state.settings) as conn:
        result = service.read(conn, principal, patient_id, encounter_id)
        audit.append(conn, principal, "encounter.read", encounter_id)
        return tagged(response, result)


@router.put("/{encounter_id}", response_model=EncounterRecord)
def update(
    patient_id: UUID,
    encounter_id: UUID,
    data: EncounterUpdate,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return tagged(
            response,
            service.change(
                conn, principal, patient_id, encounter_id, expected_version(if_match), data
            ),
        )


@router.post("/{encounter_id}/status", response_model=EncounterRecord)
def transition(
    patient_id: UUID,
    encounter_id: UUID,
    data: Transition,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return tagged(
            response,
            service.change(
                conn,
                principal,
                patient_id,
                encounter_id,
                expected_version(if_match),
                data,
                transition=True,
            ),
        )


@router.post("/{encounter_id}/addenda", status_code=201, response_model=EncounterRecord)
def addendum(
    patient_id: UUID,
    encounter_id: UUID,
    data: AddendumCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return tagged(response, service.addendum(conn, principal, patient_id, encounter_id, data))
