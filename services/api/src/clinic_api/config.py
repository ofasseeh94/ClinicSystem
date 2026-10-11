"""Explicit environment configuration; no production development-auth fallback."""

import os
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default="", repr=False)
    environment: str = "development"
    dev_token: str = field(default="", repr=False)
    dev_clinic_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""

    def __post_init__(self):
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("Unsupported application environment")
        if self.dev_token and len(self.dev_token) < 32:
            raise ValueError("Development token must contain at least 32 characters")
        if self.environment == "production":
            if self.dev_token:
                raise ValueError("Development authentication is forbidden in production")
            if not (
                self.oidc_issuer.startswith("https://")
                and self.oidc_jwks_url.startswith("https://")
                and self.oidc_audience
                and self.database_url
            ):
                raise ValueError("Production requires PostgreSQL and managed OIDC configuration")

    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            environment=os.getenv("APP_ENV", "development"),
            dev_token=os.getenv("DEV_AUTH_TOKEN", ""),
            dev_clinic_id=UUID(os.getenv("DEV_CLINIC_ID", str(cls.dev_clinic_id))),
            oidc_issuer=os.getenv("OIDC_ISSUER", ""),
            oidc_audience=os.getenv("OIDC_AUDIENCE", ""),
            oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
        )
