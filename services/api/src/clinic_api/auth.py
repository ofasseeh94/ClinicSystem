"""OIDC bearer validation and explicitly local synthetic-data authentication."""

import secrets
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Request
from fastapi.security import HTTPBearer

from .errors import Problem

bearer = HTTPBearer(auto_error=False)
ROLE_PERMISSIONS = {
    "registrar": {"patient:read", "patient:create", "patient:edit", "form:read", "form:write"},
    "clinician": {"patient:read", "patient:create", "patient:edit", "form:read", "form:write"},
    "auditor": {"audit:read"},
    "admin": {
        "patient:read",
        "patient:create",
        "patient:edit",
        "form:read",
        "form:write",
        "audit:read",
    },
}
ROLE_PERMISSIONS["registrar"].add("encounter:read")
ROLE_PERMISSIONS['registrar'].update({'document:read','document:write','investigation:read'})
for clinical_role in ("clinician", "admin"):
    ROLE_PERMISSIONS[clinical_role].update({"encounter:read", "encounter:write"})
    ROLE_PERMISSIONS[clinical_role].update({'document:read','document:write','investigation:read','investigation:write'})


@dataclass(frozen=True)
class Principal:
    actor_id: str
    clinic_id: UUID
    roles: tuple[str, ...]

    def require(self, permission):
        if not any(permission in ROLE_PERMISSIONS.get(role, set()) for role in self.roles):
            raise Problem(403, "forbidden", "Your role cannot perform this action.")


async def authenticate(request: Request):
    credentials = await bearer(request)
    if not credentials:
        raise Problem(401, "unauthorized", "Staff authentication is required.")
    settings = request.app.state.settings
    if settings.environment in {"development", "test"}:
        if not settings.dev_token:
            raise Problem(503, "auth_unconfigured", "Development access has not been configured.")
        if not secrets.compare_digest(credentials.credentials, settings.dev_token):
            raise Problem(401, "unauthorized", "Staff credentials are invalid.")
        return Principal("synthetic-development-staff", settings.dev_clinic_id, ("admin",))
    try:
        key = request.app.state.jwks.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={"require": ["exp", "iat", "sub", "iss", "aud", "clinic_id", "roles"]},
        )
        roles = claims["roles"]
        if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
            raise ValueError("Invalid roles")
        if not isinstance(claims["sub"], str) or not claims["sub"]:
            raise ValueError("Invalid subject")
        return Principal(claims["sub"], UUID(claims["clinic_id"]), tuple(roles))
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise Problem(401, "unauthorized", "Staff credentials are invalid.") from None
