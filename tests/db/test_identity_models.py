"""Pure tests use MS-002 schemas, without substituting SQLite for PostgreSQL."""

from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect

from benefitbridge.db.base import subject_hmac
from benefitbridge.db.profiles import FactValueJson
from benefitbridge.domain.enums import FactType
from benefitbridge.domain.facts import GpaValue


def test_deny_ledger_hmac_is_stable_keyed_and_minimal():
    subject = UUID("00000000-0000-4000-8000-000000000001")
    digest = subject_hmac(subject, b"synthetic-key" * 3)
    assert len(digest) == 32
    assert subject_hmac(subject, b"synthetic-key" * 3) == digest
    assert subject_hmac(subject, b"different-key" * 3) != digest
    assert subject_hmac(UUID(int=2), b"synthetic-key" * 3) != digest
    with pytest.raises(ValueError, match="32 bytes"):
        subject_hmac(subject, b"short")


def test_fact_storage_round_trip_preserves_original_gpa_scale():
    codec = FactValueJson()
    value = GpaValue(type=FactType.GPA, number="3.50", scale_max="5.00")
    stored = codec.process_bind_param(value, dialect())
    assert stored == {"type": "GPA", "number": "3.50", "scale_max": "5.00"}
    assert codec.process_result_value(stored, dialect()) == value
    with pytest.raises(ValidationError):
        codec.process_result_value({"type": "GPA", "number": "3.50"}, dialect())
