from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from ..encounters.schemas import past_time
from ..registry.schemas import StrictModel


class DocumentCreate(StrictModel):
    request_id: UUID
    encounter_id: UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    category: Literal["lab", "imaging", "letter", "other"]
    captured_at: datetime
    source: str = Field(min_length=1, max_length=500)
    _time = field_validator("captured_at")(past_time)


class DocumentRecord(StrictModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID | None
    title: str
    category: str
    captured_at: datetime
    source: str
    state: str
    mime_type: str | None
    byte_size: int | None
    sha256: str | None
    scan_detail: str
    version: int
    created_by: str
    created_at: datetime
    withdrawal_reason: str | None


class DocumentPage(StrictModel):
    items: list[DocumentRecord]
    total: int
    page: int
    scan_mode: str


class Reason(StrictModel):
    reason: str = Field(min_length=5, max_length=500)


class Ticket(StrictModel):
    ticket: str
    expires_in: int


class Download(StrictModel):
    ticket: str = Field(min_length=1, max_length=3000)


class OrderCreate(StrictModel):
    request_id: UUID
    encounter_id: UUID
    test_name: str = Field(min_length=1, max_length=160)
    indication: str = Field(min_length=1, max_length=2000)
    priority: Literal["routine", "urgent"] = "routine"


class OrderStatus(Reason):
    status: Literal["in_progress", "completed", "cancelled"]


class OrderRecord(StrictModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID
    test_name: str
    indication: str
    priority: str
    status: str
    version: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    cancellation_reason: str | None


class ResultCreate(Reason):
    request_id: UUID
    order_id: UUID | None = None
    document_id: UUID | None = None
    supersedes_id: UUID | None = None
    test_name: str = Field(min_length=1, max_length=160)
    collected_at: datetime
    value: str = Field(min_length=1, max_length=2000)
    unit: str = Field(default="", max_length=160)
    reference_range: str = Field(default="", max_length=500)
    interpretation: str = Field(default="", max_length=2000)
    source: str = Field(min_length=1, max_length=500)
    _time = field_validator("collected_at")(past_time)


class ResultRecord(StrictModel):
    id: UUID
    patient_id: UUID
    order_id: UUID | None
    document_id: UUID | None
    supersedes_id: UUID | None
    test_name: str
    collected_at: datetime
    value: str
    unit: str
    reference_range: str
    interpretation: str
    source: str
    reason: str
    created_by: str
    created_at: datetime
    corrected_by_id: UUID | None = None


class InvestigationPage(StrictModel):
    orders: list[OrderRecord]
    results: list[ResultRecord]
    orders_total: int
    results_total: int
    page: int
