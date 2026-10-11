from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from ..registry.schemas import StrictModel


def past_time(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone is required")
    if value > datetime.now(timezone.utc):
        raise ValueError("Future observations are not allowed")
    if value.year < 1900:
        raise ValueError("Observation date is invalid")
    return value


class Note(StrictModel):
    history: str = Field(default="", max_length=10000)
    examination: str = Field(default="", max_length=10000)
    assessment: str = Field(default="", max_length=10000)
    plan: str = Field(default="", max_length=10000)
    allergy_review: Literal["not_reviewed", "reviewed"] = "not_reviewed"
    medication_review: Literal["not_reviewed", "reviewed"] = "not_reviewed"


class Measurement(StrictModel):
    measured_at: datetime
    weight_kg: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    length_cm: float | None = Field(default=None, gt=0, le=400, allow_inf_nan=False)
    head_cm: float | None = Field(default=None, gt=0, le=200, allow_inf_nan=False)
    position: Literal["recumbent", "standing", "unknown"] = "unknown"
    technique: str = Field(min_length=1, max_length=300)
    equipment: str = Field(min_length=1, max_length=300)
    source: Literal["clinic", "guardian_report", "external_record"]

    _time = field_validator("measured_at")(past_time)

    @model_validator(mode="after")
    def has_value(self):
        if all(v is None for v in (self.weight_kg, self.length_cm, self.head_cm)):
            raise ValueError("At least one measurement is required")
        return self


class EncounterCreate(StrictModel):
    request_id: UUID
    occurred_at: datetime
    reason: str = Field(min_length=1, max_length=1000)
    consent_context: str = Field(min_length=1, max_length=1000)

    _time = field_validator("occurred_at")(past_time)


class EncounterUpdate(StrictModel):
    note: Note
    measurements: list[Measurement] = Field(default_factory=list, max_length=50)
    audit_reason: str = Field(min_length=5, max_length=500)


class Transition(StrictModel):
    status: Literal["draft", "in_review", "signed", "cancelled"]
    reason: str = Field(min_length=5, max_length=500)


class AddendumCreate(StrictModel):
    request_id: UUID
    reason: str = Field(min_length=5, max_length=500)
    content: str = Field(min_length=1, max_length=10000)


class Addendum(StrictModel):
    id: UUID
    reason: str
    content: str
    signed_by: str
    signed_at: datetime


class EncounterRecord(StrictModel):
    id: UUID
    patient_id: UUID
    occurred_at: datetime
    reason: str
    consent_context: str
    birth_context: dict
    note: Note
    measurements: list[Measurement]
    status: Literal["draft", "in_review", "signed", "cancelled"]
    version: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    signed_by: str | None
    signed_at: datetime | None
    cancellation_reason: str | None
    addenda: list[Addendum]


class EncounterPage(StrictModel):
    items: list[EncounterRecord]
    total: int
    page: int
