from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from ..auth import Principal, authenticate
from ..database import connect
from ..errors import Problem
from ..registry import audit
from ..registry.routes import expected_version
from ..registry.schemas import ProblemResponse
from . import files, service
from .schemas import (
    DocumentCreate,
    DocumentPage,
    DocumentRecord,
    Download,
    InvestigationPage,
    OrderCreate,
    OrderRecord,
    OrderStatus,
    Reason,
    ResultCreate,
    ResultRecord,
    Ticket,
)

router = APIRouter(
    prefix="/v1/patients/{patient_id}",
    tags=["Documents and investigations"],
    responses={
        s: {
            "model": ProblemResponse,
            "description": "Problem response; supplied values are never echoed",
        }
        for s in (400, 401, 403, 404, 409, 412, 413, 415, 422, 428, 503)
    },
)


@router.post("/documents", response_model=DocumentRecord, status_code=201)
def create_document(
    patient_id: UUID,
    data: DocumentCreate,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.create_document(
            conn, request.app.state.settings, principal, patient_id, data
        )


@router.get("/documents", response_model=DocumentPage)
def documents(
    patient_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    principal: Principal = Depends(authenticate),
):
    principal.require("document:read")
    with connect(request.app.state.settings) as conn:
        service.scope(conn, principal, patient_id)
        fields = ",".join(DocumentRecord.model_fields)
        rows = conn.execute(
            f"SELECT {fields} FROM documents WHERE clinic_id=%s AND patient_id=%s ORDER BY captured_at DESC,id LIMIT 20 OFFSET %s",
            (principal.clinic_id, patient_id, (page - 1) * 20),
        ).fetchall()
        total = conn.execute(
            "SELECT count(*) AS n FROM documents WHERE clinic_id=%s AND patient_id=%s",
            (principal.clinic_id, patient_id),
        ).fetchone()["n"]
        audit.append(
            conn,
            principal,
            "document.list",
            patient_id,
            after={"returned_ids": [str(r["id"]) for r in rows]},
        )
        return {
            "items": [service.public(r, "document") for r in rows],
            "total": total,
            "page": page,
            "scan_mode": request.app.state.settings.document_scan_mode,
        }


@router.put(
    "/documents/{document_id}/content",
    response_model=DocumentRecord,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                m: {"schema": {"type": "string", "format": "binary"}}
                for m in ("application/pdf", "image/png", "image/jpeg")
            },
        }
    },
)
async def upload(
    patient_id: UUID,
    document_id: UUID,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    principal.require("document:write")

    def check_scope():
        with connect(request.app.state.settings) as conn:
            service.raw(conn, principal, patient_id, "document", document_id)

    await run_in_threadpool(check_scope)
    content = bytearray()
    async for part in request.stream():
        if len(content) + len(part) > files.MAX_BYTES:
            raise Problem(413, "file_size", "Attachments must contain 1 byte to 10 MiB.")
        content.extend(part)
    mime = request.headers.get("content-type", "").split(";")[0].strip().lower()

    def store():
        with connect(request.app.state.settings) as conn:
            return service.upload(
                conn,
                request.app.state.settings,
                principal,
                patient_id,
                document_id,
                bytes(content),
                mime,
            )

    return await run_in_threadpool(store)


@router.post("/documents/{document_id}/rescan", response_model=DocumentRecord)
def rescan(
    patient_id: UUID,
    document_id: UUID,
    data: Reason,
    request: Request,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.change_document(
            conn,
            request.app.state.settings,
            principal,
            patient_id,
            document_id,
            expected_version(if_match),
            data.reason,
            False,
        )


@router.post("/documents/{document_id}/withdraw", response_model=DocumentRecord)
def withdraw(
    patient_id: UUID,
    document_id: UUID,
    data: Reason,
    request: Request,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.change_document(
            conn,
            request.app.state.settings,
            principal,
            patient_id,
            document_id,
            expected_version(if_match),
            data.reason,
            True,
        )


@router.post("/documents/{document_id}/ticket", response_model=Ticket)
def ticket(
    patient_id: UUID,
    document_id: UUID,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.ticket(conn, request.app.state.settings, principal, patient_id, document_id)


@router.post(
    "/documents/{document_id}/download",
    response_class=Response,
    responses={
        200: {
            "description": "Authorized attachment bytes",
            "content": {
                m: {"schema": {"type": "string", "format": "binary"}}
                for m in ("application/pdf", "image/png", "image/jpeg")
            },
        }
    },
)
def download(
    patient_id: UUID,
    document_id: UUID,
    data: Download,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        content, mime = service.download(
            conn, request.app.state.settings, principal, patient_id, document_id, data.ticket
        )
    suffix = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}[mime]
    return Response(
        content,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="attachment-{document_id}.{suffix}"',
            "Content-Security-Policy": "sandbox; default-src 'none'",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.get("/investigations", response_model=InvestigationPage)
def investigations(
    patient_id: UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    principal: Principal = Depends(authenticate),
):
    principal.require("investigation:read")
    with connect(request.app.state.settings) as conn:
        service.scope(conn, principal, patient_id)
        orders = conn.execute(
            "SELECT * FROM investigation_orders WHERE clinic_id=%s AND patient_id=%s ORDER BY created_at DESC,id LIMIT 20 OFFSET %s",
            (principal.clinic_id, patient_id, (page - 1) * 20),
        ).fetchall()
        results = conn.execute(
            "SELECT r.*,c.id AS corrected_by_id FROM investigation_results r LEFT JOIN investigation_results c ON c.clinic_id=r.clinic_id AND c.supersedes_id=r.id WHERE r.clinic_id=%s AND r.patient_id=%s ORDER BY r.collected_at DESC,r.created_at DESC,r.id LIMIT 20 OFFSET %s",
            (principal.clinic_id, patient_id, (page - 1) * 20),
        ).fetchall()
        totals = [
            conn.execute(
                f"SELECT count(*) AS n FROM {table} WHERE clinic_id=%s AND patient_id=%s",
                (principal.clinic_id, patient_id),
            ).fetchone()["n"]
            for table in ("investigation_orders", "investigation_results")
        ]
        audit.append(
            conn,
            principal,
            "investigation.list",
            patient_id,
            after={
                "order_ids": [str(r["id"]) for r in orders],
                "result_ids": [str(r["id"]) for r in results],
            },
        )
        return {
            "orders": [service.public(r, "order") for r in orders],
            "results": [service.public(r, "result") for r in results],
            "orders_total": totals[0],
            "results_total": totals[1],
            "page": page,
        }


@router.post("/investigation-orders", response_model=OrderRecord, status_code=201)
def order(
    patient_id: UUID,
    data: OrderCreate,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.create_order(conn, principal, patient_id, data)


@router.post("/investigation-orders/{order_id}/status", response_model=OrderRecord)
def order_status(
    patient_id: UUID,
    order_id: UUID,
    data: OrderStatus,
    request: Request,
    if_match: str | None = Header(default=None),
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.change_order(
            conn, principal, patient_id, order_id, expected_version(if_match), data
        )


@router.post("/investigation-results", response_model=ResultRecord, status_code=201)
def result(
    patient_id: UUID,
    data: ResultCreate,
    request: Request,
    principal: Principal = Depends(authenticate),
):
    with connect(request.app.state.settings) as conn:
        return service.create_result(conn, request.app.state.settings, principal, patient_id, data)
