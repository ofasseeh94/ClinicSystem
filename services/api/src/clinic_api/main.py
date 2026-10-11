"""Foundation API; no patient data or clinical behavior."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Pediatric Clinic API", version="0.0.1")


class HealthResponse(BaseModel):
    status: str = "ok"


@app.get("/health", response_model=HealthResponse, operation_id="health")
def health() -> HealthResponse:
    """Process health only; does not check dependencies."""
    return HealthResponse()
