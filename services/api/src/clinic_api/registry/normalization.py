import re
import unicodedata
from datetime import date

_TRANSLATION = str.maketrans("أإآٱى٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "ااااي01234567890123456789")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).translate(_TRANSLATION).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c) and c != "ـ")
    return " ".join(value.split())


def phone(value: str) -> str:
    value = value.translate(_TRANSLATION)
    value = re.sub(r"[ ()-]", "", value)
    if value.startswith("00"):
        value = "+" + value[2:]
    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", value):
        raise ValueError("Use an international phone number, for example +201000000000")
    return value


def age_label(dob: date, precision: str, at: date) -> str:
    if precision != "exact":
        return "Age uncertain"
    if dob > at:
        raise ValueError("Birth date is after the reference date")
    months = (at.year - dob.year) * 12 + at.month - dob.month - (at.day < dob.day)
    if months < 1:
        return f"{(at - dob).days} days"
    years, remaining = divmod(months, 12)
    return f"{years} years {remaining} months" if years else f"{months} months"
