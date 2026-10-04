"""Synthetic Unicode and page-boundary provenance; ordinary CI is network-denied."""

from hashlib import sha256
from uuid import UUID

import pytest
from pydantic import ValidationError

from benefitbridge.domain.dto import Evidence, Source, SourceSpan
from benefitbridge.domain.enums import Authority, Completeness
from benefitbridge.sources.contracts import (
    PAGE_SEPARATOR,
    DocumentText,
    NormalizedText,
    SourceSnapshot,
    normalize_document,
    normalize_pages,
    normalize_text,
    normalized_text_hash,
)

SPAN_ID = UUID("00000000-0000-4000-8000-000000000001")
DOCUMENT_ID = UUID("00000000-0000-4000-8000-000000000002")
VERSION_ID = UUID("00000000-0000-4000-8000-000000000003")


def test_nfc_lf_normalization_is_idempotent_and_preserves_context():
    raw = "  Cafe\u0301\r\nApplicants must NOT be enrolled.\r\t①  "
    expected = "  Café\nApplicants must NOT be enrolled.\n\t①  "
    assert normalize_text(raw) == expected
    assert normalize_text(expected) == expected
    assert normalized_text_hash(raw) == sha256(expected.encode("utf-8")).hexdigest()
    assert normalized_text_hash(raw) != sha256(raw.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("text", ["", "🙂é中文", "A\n\f\nB", "not eligible", "\u202euntrusted"])
def test_document_json_round_trip(text):
    normalized = normalize_document(text)
    assert NormalizedText.model_validate_json(normalized.model_dump_json()) == normalized


def test_offsets_count_code_points_not_bytes_or_utf16_units():
    document = normalize_document("A🙂e\u0301中文")
    span = document.source_span(SPAN_ID, 1, 4)
    assert span.quote == "🙂é中"
    assert span.end - span.start == 3
    assert len(span.quote.encode("utf-8")) == 9
    assert len(span.quote.encode("utf-16-le")) // 2 == 4
    document.validate_span(SourceSpan.model_validate_json(span.model_dump_json()))


@pytest.mark.parametrize("start,end", [(-1, 1), (0, 99), (3, 2), (2, 2), (True, 2), (0, 1.0)])
def test_invalid_offsets_are_not_clamped(start, end):
    with pytest.raises(ValueError, match="offsets"):
        normalize_document("abc").slice(start, end)


def test_same_length_invented_quote_is_rejected():
    normalized = normalize_document("not eligible")
    span = SourceSpan(id=SPAN_ID, page=None, start=0, end=3, quote="yes")
    with pytest.raises(ValueError, match="exact normalized"):
        normalized.validate_span(span)


def test_quote_validation_does_not_normalize_after_offsets_are_published():
    normalized = normalize_document("e\u0301X")
    span = SourceSpan(id=SPAN_ID, page=None, start=0, end=2, quote="e\u0301")
    with pytest.raises(ValueError, match="exact normalized"):
        normalized.validate_span(span)


def test_pdf_markers_include_blank_pages_and_page_local_citations():
    normalized = normalize_pages(["First🙂", "", "Third\r\npage"])
    assert normalized.text == "First🙂" + PAGE_SEPARATOR * 2 + "Third\npage"
    assert [(p.page, p.start, p.end) for p in normalized.pages] == [
        (1, 0, 6),
        (2, 9, 9),
        (3, 12, 22),
    ]
    assert normalized.source_span(SPAN_ID, 0, 5, page=3).quote == "Third"
    assert normalized.citation_hash(2) == sha256(b"").hexdigest()
    assert NormalizedText.model_validate_json(normalized.model_dump_json()) == normalized


@pytest.mark.parametrize("page", [None, 0, 4, True, 1.0])
def test_pdf_requires_an_existing_explicit_page(page):
    with pytest.raises(ValueError):
        normalize_pages(["one", "two", "three"]).slice(0, 1, page=page)


def test_spans_cannot_cross_pdf_page_boundaries_or_include_separators():
    normalized = normalize_pages(["must not", "be enrolled"])
    with pytest.raises(ValueError, match="offsets"):
        normalized.slice(0, 10, page=1)
    with pytest.raises(ValueError, match="offsets"):
        normalized.slice(8, 9, page=1)


def test_form_feeds_in_page_content_are_not_inferred_boundaries():
    normalized = normalize_pages(["A\n\f\nB", "C"])
    assert len(normalized.pages) == 2
    assert normalized.page_text(1) == "A\n\f\nB"
    assert normalized.source_span(SPAN_ID, 1, 4, page=1).quote == PAGE_SEPARATOR


@pytest.mark.parametrize(
    "changes",
    [
        {"normalized_text_hash": "0" * 64},
        {"text": "e\u0301"},
        {"normalization_version": "future"},
        {"unexpected": "private content"},
    ],
)
def test_stored_normalized_contract_rejects_tampering(changes):
    payload = normalize_document("é").model_dump(mode="json")
    with pytest.raises(ValidationError):
        NormalizedText.model_validate({**payload, **changes})


@pytest.mark.parametrize(
    "changes",
    [
        {"page": 2},
        {"start": 1},
        {"end": 99},
        {"normalized_text_hash": "0" * 64},
    ],
)
def test_page_markers_reject_inconsistent_coordinates_or_hashes(changes):
    payload = normalize_pages(["one", "two"]).model_dump(mode="json")
    payload["pages"][0].update(changes)
    with pytest.raises(ValidationError):
        NormalizedText.model_validate(payload)


def test_aggregate_hash_binds_page_boundaries():
    assert (
        normalize_pages(["ab", "c"]).normalized_text_hash
        != normalize_pages(["a", "bc"]).normalized_text_hash
    )


def test_recorded_boundary_cannot_be_replaced_by_content():
    payload = normalize_pages(["one", "two"]).model_dump(mode="json")
    payload["text"] = "one---two"
    payload["normalized_text_hash"] = normalized_text_hash(payload["text"])
    with pytest.raises(ValidationError, match="separator"):
        NormalizedText.model_validate(payload)


def test_blank_page_cannot_yield_nonempty_evidence():
    normalized = normalize_pages([""])
    assert normalized.page_text(1) == ""
    with pytest.raises(ValueError, match="offsets"):
        normalized.source_span(SPAN_ID, 0, 1, page=1)


def test_document_evidence_requires_explicit_pages():
    with pytest.raises(ValidationError, match="page markers"):
        DocumentText(
            document_id=DOCUMENT_ID,
            document_version_id=VERSION_ID,
            normalized=normalize_document("synthetic text"),
            raw_file_hash="0" * 64,
        )


def test_invalid_unicode_cannot_produce_a_partial_digest():
    with pytest.raises(ValueError, match="Unicode scalar"):
        normalize_document("private\ud800content")


def test_document_evidence_round_trip_and_version_binding():
    document = DocumentText(
        document_id=DOCUMENT_ID,
        document_version_id=VERSION_ID,
        normalized=normalize_pages(["Café🙂", "Evidence"]),
        raw_file_hash=sha256(b"synthetic PDF bytes").hexdigest(),
    )
    evidence = document.evidence(SPAN_ID, 2, 0, 8)
    document.validate_evidence(Evidence.model_validate_json(evidence.model_dump_json()))
    assert evidence.normalized_text_hash == sha256(b"Evidence").hexdigest()
    assert evidence.normalized_text_hash != document.raw_file_hash
    assert DocumentText.model_validate_json(document.model_dump_json()) == document
    for changes in (
        {"document_version_id": SPAN_ID},
        {"document_id": SPAN_ID},
        {"normalized_text_hash": document.raw_file_hash},
    ):
        changed = Evidence.model_validate({**evidence.model_dump(), **changes})
        with pytest.raises(ValueError):
            document.validate_evidence(changed)


@pytest.mark.parametrize("authority", list(Authority))
def test_source_snapshot_reuses_explicit_authority_and_public_dto(authority, fake_clock):
    normalized = normalize_document("Applicants must be enrolled.")
    source = Source(
        id=DOCUMENT_ID,
        snapshot_id=VERSION_ID,
        url="https://synthetic.example.invalid/policy",
        retrieved_at=fake_clock.now(),
        content_hash=normalized.normalized_text_hash,
        authority=authority,
        completeness=Completeness.INCOMPLETE,
        spans=(normalized.source_span(SPAN_ID, 0, len(normalized.text)),),
    )
    snapshot = SourceSnapshot(
        source=source,
        normalized=normalized,
        raw_file_hash=sha256(b"<html>synthetic</html>").hexdigest(),
    )
    assert snapshot.source.authority == authority
    assert snapshot.source.completeness == Completeness.INCOMPLETE
    assert SourceSnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot
    with pytest.raises(ValidationError):
        SourceSnapshot(
            source=Source.model_validate(
                {**source.model_dump(), "content_hash": snapshot.raw_file_hash}
            ),
            normalized=normalized,
            raw_file_hash=snapshot.raw_file_hash,
        )


def test_snapshots_do_not_promote_a_same_length_false_quote(fake_clock):
    normalized = normalize_document("not")
    source = Source(
        id=DOCUMENT_ID,
        snapshot_id=VERSION_ID,
        url="https://synthetic.example.invalid/policy",
        retrieved_at=fake_clock.now(),
        content_hash=normalized.normalized_text_hash,
        authority=Authority.DISCOVERY_ONLY,
        completeness=Completeness.INCOMPLETE,
        spans=(SourceSpan(id=SPAN_ID, page=None, start=0, end=3, quote="yes"),),
    )
    with pytest.raises(ValidationError, match="exact normalized"):
        SourceSnapshot(source=source, normalized=normalized, raw_file_hash="0" * 64)


def test_immutable_normalized_text_hides_content_from_repr():
    normalized = normalize_document("synthetic private content")
    assert normalized.text not in repr(normalized)
    with pytest.raises(ValidationError):
        normalized.text = "changed"
