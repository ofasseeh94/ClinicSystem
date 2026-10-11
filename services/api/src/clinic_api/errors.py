from fastapi.responses import JSONResponse


class Problem(Exception):
    def __init__(self, status: int, code: str, detail: str, **extras):
        self.status, self.code, self.detail, self.extras = status, code, detail, extras


def problem_response(request, exc: Problem):
    return JSONResponse(
        status_code=exc.status,
        media_type="application/problem+json",
        content={
            "type": f"urn:clinic:problem:{exc.code}",
            "title": exc.code,
            "status": exc.status,
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", ""),
            **exc.extras,
        },
    )
