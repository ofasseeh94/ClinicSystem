from decimal import Decimal
from math import isfinite

from ..errors import Problem
from .schemas import FormSubmission


def definition(conn, key, version):
    row = conn.execute(
        "SELECT form_key,version,schema,published_at FROM form_definitions "
        "WHERE form_key=%s AND version=%s",
        (key, version),
    ).fetchone()
    if not row:
        raise Problem(404, "form_not_found", "That published form version does not exist.")
    return row


def validate_submission(conn, submission: FormSubmission):
    schema = definition(conn, submission.form_key, submission.version)["schema"]
    fields = {f["key"]: f for f in schema["fields"]}
    if set(submission.answers) - set(fields):
        raise Problem(422, "invalid_form", "The form contains unsupported field keys.")
    for key, field in fields.items():
        value = submission.answers.get(key)
        if value is None:
            if field.get("required"):
                raise Problem(422, "invalid_form", "A required background field is missing.")
            continue
        kind = field["type"]
        valid = False
        if kind == "enum":
            valid = isinstance(value, str) and value in field["options"]
        elif kind == "text":
            valid = isinstance(value, str) and len(value) <= field.get("max_length", 2000)
        elif kind in {"integer", "number"}:
            valid = type(value) in ({int} if kind == "integer" else {int, float})
            if valid and isinstance(value, float):
                valid = isfinite(value)
            if valid:
                valid = (
                    Decimal(str(field["min"])) <= Decimal(str(value)) <= Decimal(str(field["max"]))
                )
        if not valid:
            raise Problem(422, "invalid_form", f"Invalid value for background field {key}.")
    return schema
