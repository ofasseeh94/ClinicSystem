from datetime import date

import pytest
from clinic_api.registry.normalization import age_label, normalize, phone
from clinic_api.registry.schemas import PatientCreate
from pydantic import ValidationError


def test_arabic_and_english_normalization():
    assert normalize(" أَحـمَد  علي ") == "احمد علي"
    assert normalize("ÉMILY  Test") == "emily test"
    assert normalize("٠١٢٣٤") == "01234"


def test_phone_normalization():
    assert phone("0020 (100) 000-0001") == "+201000000001"
    with pytest.raises(ValueError):
        phone("01000000001")


def test_age_uses_reference_date_and_uncertainty():
    assert age_label(date(2024, 6, 15), "exact", date(2026, 6, 14)) == "1 years 11 months"
    assert age_label(date(2024, 6, 15), "exact", date(2024, 6, 20)) == "5 days"
    assert age_label(date(2024, 6, 15), "estimated", date(2026, 6, 14)) == "Age uncertain"
    assert age_label(date(2024, 2, 29), "exact", date(2025, 2, 28)) == "11 months"


def test_identity_and_allergy_unknown_states(patient_data):
    assert PatientCreate(**patient_data).allergy_review_status == "unknown"
    with pytest.raises(ValidationError):
        PatientCreate(**{**patient_data, "name_ar": "", "name_en": ""})
    with pytest.raises(ValidationError):
        PatientCreate(**{**patient_data, "dob": "2999-01-01"})
    with pytest.raises(ValidationError):
        PatientCreate(**{**patient_data, "allergy_review_status": "known"})
    with pytest.raises(ValidationError):
        PatientCreate(
            **{
                **patient_data,
                "allergy_review_status": "no_known",
                "allergies": [{"substance": "Synthetic substance", "reaction": "Reported rash"}],
            }
        )
