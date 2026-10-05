"""MS-006 coordinate spaces survive the MS-014 typed persistence boundary."""

from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect
from tests.fakes.providers import FakeClock

from benefitbridge.db.sources import ModelJson, OpportunityMetadata, snapshot_record, span_record
from benefitbridge.domain.dto import Source
from benefitbridge.domain.enums import Authority, Completeness
from benefitbridge.sources.contracts import NormalizedText, SourceSnapshot, normalize_pages


def test_normalized_json_round_trip_and_page_citation(fake_clock: FakeClock) -> None:
    normalized = normalize_pages(["First page.", "Applicants must be enrolled."])
    span = normalized.source_span(UUID(int=4), 0, 28, page=2)
    contract = SourceSnapshot(
        source=Source(
            id=UUID(int=1),
            snapshot_id=UUID(int=2),
            url="https://example.invalid/policy",
            retrieved_at=fake_clock.now(),
            content_hash=normalized.normalized_text_hash,
            authority=Authority.OFFICIAL,
            completeness=Completeness.COMPLETE,
            spans=(span,),
        ),
        normalized=normalized,
        raw_file_hash="a" * 64,
    )
    record = snapshot_record(contract, text_object_key="public/synthetic-policy")
    assert record.retrieved_at == fake_clock.now()
    assert record.raw_hash != record.normalized_hash
    assert span_record(record.id, normalized, span).quote == span.quote
    codec = ModelJson(NormalizedText)
    assert (
        codec.process_result_value(codec.process_bind_param(normalized, dialect()), dialect())
        == normalized
    )
    assert codec.process_bind_param(None, dialect()) is None
    broken = normalized.model_dump(mode="json")
    broken["text"] = "Invented text"
    with pytest.raises(ValidationError):
        codec.process_result_value(broken, dialect())


def test_wrong_quote_is_rejected_before_sql() -> None:
    normalized = normalize_pages(["ABC"])
    span = normalized.source_span(UUID(int=4), 0, 3, page=1)
    with pytest.raises(ValueError, match="exact normalized"):
        span_record(UUID(int=2), normalized, span.model_copy(update={"quote": "XYZ"}))


def test_public_metadata_rejects_applicant_fields() -> None:
    with pytest.raises(ValidationError):
        OpportunityMetadata.model_validate(
            {"owner_id": str(UUID(int=1)), "evaluation_id": str(UUID(int=2))}
        )
