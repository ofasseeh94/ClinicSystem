from datetime import date, datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator

from ..encounters.schemas import past_time
from ..registry.schemas import StrictModel


class CatalogInput(StrictModel):
    request_id: UUID
    product_name: str = Field(min_length=1, max_length=160)
    generic_name: str = Field(min_length=1, max_length=160)
    formulation: str = Field(min_length=1, max_length=160)
    strength_text: str = Field(min_length=1, max_length=500)
    route_text: str = Field(min_length=1, max_length=160)
    source_kind: Literal["synthetic", "regulatory_label", "formulary"]
    source_title: str = Field(min_length=1, max_length=500)
    source_publisher: str = Field(min_length=1, max_length=160)
    source_version: str = Field(min_length=1, max_length=160)
    source_url: str = Field(default="", max_length=2000)
    source_country: str = Field(min_length=2, max_length=80)
    source_checked_on: date

    @field_validator("source_url")
    @classmethod
    def safe_url(cls, value):
        if value:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Use an HTTPS source URL without credentials")
        return value

    @field_validator("source_checked_on")
    @classmethod
    def checked_date(cls, value):
        if value > datetime.now(ZoneInfo("Africa/Cairo")).date() or value.year < 1900:
            raise ValueError("Source check date is invalid")
        return value


class CatalogRecord(CatalogInput):
    id: UUID
    catalog_id: UUID
    version: int
    state: str
    revision: int
    created_by: str
    created_at: datetime
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_reason: str | None


class CatalogTransition(StrictModel):
    state: Literal["draft", "in_review", "verified_identity", "retired"]
    reason: str = Field(min_length=5, max_length=1000)


class CatalogPage(StrictModel):
    items: list[CatalogRecord]
    total: int
    page: int


class StatementInput(StrictModel):
    request_id: UUID
    encounter_id: UUID | None = None
    catalog_version_id: UUID | None = None
    supersedes_id: UUID | None = None
    medication_name: str = Field(min_length=1, max_length=160)
    reported_instructions: str = Field(default="", max_length=2000)
    use_status: Literal["active", "stopped", "completed", "unknown"] = "unknown"
    recorded_for: datetime
    source: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=5, max_length=500)
    _time = field_validator("recorded_for")(past_time)


class StatementRecord(StatementInput):
    id: UUID
    patient_id: UUID
    created_by: str
    created_at: datetime
    corrected_by_id: UUID | None = None


class StatementPage(StrictModel):
    items: list[StatementRecord]
    total: int
    page: int


class Capabilities(StrictModel):
    dose_calculation_enabled: bool = False
    prescribing_enabled: bool = False
    verification_scope: str = "catalog_identity_only"
    prerequisites: list[str] = [
        "Approved pediatric dose sources",
        "Independent clinical/pharmacist verification",
        "Validated dose/max/interaction rules and fixtures",
        "Clinical and production release review",
    ]
