from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .normalization import phone


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Guardian(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    phone_e164: str = Field(max_length=30)
    relation: Literal["mother", "father", "guardian", "other", "unknown"] = "unknown"

    @field_validator("phone_e164")
    @classmethod
    def validate_phone(cls, value):
        return phone(value)


class Allergy(StrictModel):
    substance: str = Field(min_length=1, max_length=160)
    reaction: str = Field(min_length=1, max_length=500)


class FormSubmission(StrictModel):
    form_key: str = Field(min_length=1, max_length=80)
    version: int = Field(ge=1)
    answers: dict = Field(default_factory=dict)


class PatientInput(StrictModel):
    name_ar: str = Field(default="", max_length=160)
    name_en: str = Field(default="", max_length=160)
    dob: date
    dob_precision: Literal["exact", "estimated", "month", "year"] = "exact"
    dob_source: Literal["guardian", "document", "imported", "unknown"] = "guardian"
    growth_reference_sex: Literal["female", "male", "unknown"] = "unknown"
    guardian: Guardian
    aliases: list[str] = Field(default_factory=list, max_length=10)
    allergy_review_status: Literal["unknown", "not_assessed", "no_known", "known"] = "unknown"
    allergies: list[Allergy] = Field(default_factory=list, max_length=30)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, value):
        if any(not a.strip() or len(a) > 160 for a in value):
            raise ValueError("Aliases must contain 1-160 characters")
        return list(dict.fromkeys(a.strip() for a in value))

    @model_validator(mode="after")
    def validate_patient(self):
        if not (self.name_ar or self.name_en):
            raise ValueError("Enter an Arabic or English patient name")
        # A birth-date anchor is retained for uncertain dates; precision is always explicit.
        from zoneinfo import ZoneInfo

        today = datetime.now(ZoneInfo("Africa/Cairo")).date()
        if self.dob > today or self.dob.year < 1900:
            raise ValueError("Birth date must be between 1900 and today")
        if (self.allergy_review_status == "known") != bool(self.allergies):
            raise ValueError(
                "Known allergies require substance and reaction; other states must have no allergy entries"
            )
        return self


class PatientCreate(PatientInput):
    background: FormSubmission | None = None
    duplicate_review_reason: str | None = Field(default=None, min_length=5, max_length=500)


class PatientUpdate(PatientInput):
    audit_reason: str = Field(min_length=5, max_length=500)


class SearchRequest(StrictModel):
    query: str = Field(default="", max_length=160)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)


class PatientSummary(StrictModel):
    patient_id: UUID
    clinic_code: str
    name_ar: str
    name_en: str
    dob: date
    dob_precision: str
    growth_reference_sex: str
    allergy_review_status: str
    guardian_name: str
    masked_phone: str
    version: int


class SearchResponse(StrictModel):
    items: list[PatientSummary]
    total: int
    page: int
    page_size: int


class BackgroundResponse(StrictModel):
    id: UUID
    form_key: str
    version: int
    answers: dict
    created_at: datetime
    created_by: str
    schema_definition: dict


class PatientRecord(PatientInput):
    patient_id: UUID
    clinic_code: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    status: str
    contact_authority: str
    background_responses: list[BackgroundResponse]
    warnings: list[str]


class SessionResponse(StrictModel):
    actor_id: str
    clinic_id: UUID
    roles: list[str]
    environment: str


class ProblemResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    request_id: str
    fields: list[str] | None = None
    candidates: list[PatientSummary] | None = None


class PublishedForm(BaseModel):
    form_key: str
    version: int
    schema_definition: dict = Field(alias="schema")
    published_at: datetime


class AuditResponse(BaseModel):
    items: list[dict]
    next_cursor: int
