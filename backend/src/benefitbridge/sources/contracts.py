"""Immutable normalized text and exact citations shared by source/PDF adapters.

Normalization v1 uses NFC and LF line endings only: whitespace, case, negation,
punctuation and compatibility characters retain their meaning. Offsets always
refer to the resulting text, never raw bytes or browser UTF-16 code units.
"""

from collections.abc import Sequence
from hashlib import sha256
from typing import Literal, Self
from unicodedata import normalize
from uuid import UUID

from pydantic import Field, StrictStr, model_validator

from benefitbridge.domain.base import DomainModel, NonNegativeInt, PositiveInt, Sha256
from benefitbridge.domain.dto import Evidence, Source, SourceSpan

NORMALIZATION_VERSION = "nfc-lf-v1"
PAGE_SEPARATOR = "\n\f\n"


def normalize_text(text: str) -> str:
    """Normalize before selecting offsets; never normalize an already cited quote."""
    if not isinstance(text, str):
        raise TypeError("Text must be a Unicode string")
    result = normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    try:
        result.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Text must contain UTF-8 encodable Unicode scalar values") from None
    return result


def normalized_text_hash(text: str) -> str:
    """SHA-256 of normalized UTF-8, independent of the raw resource's digest."""
    return sha256(normalize_text(text).encode("utf-8")).hexdigest()


class PageMarker(DomainModel):
    """One-based page and half-open range in the aggregate normalized text.

    Separator characters are excluded from page ranges. Empty pages remain
    markers so later extraction cannot silently renumber document evidence.
    """

    page: PositiveInt
    start: NonNegativeInt
    end: NonNegativeInt
    normalized_text_hash: Sha256

    @model_validator(mode="after")
    def ordered_range(self) -> Self:
        if self.end < self.start:
            raise ValueError("Page end cannot precede its start")
        return self


class NormalizedText(DomainModel):
    """HTML has no page markers; PDF citations must specify a recorded page.

    Aggregate text joins pages with PAGE_SEPARATOR. Evidence hashes bind the
    cited page's normalized text; public Source.content_hash binds the entire
    normalized resource, including explicit page boundaries.
    """

    normalization_version: Literal["nfc-lf-v1"]
    text: StrictStr = Field(repr=False)
    normalized_text_hash: Sha256
    pages: tuple[PageMarker, ...]

    @model_validator(mode="after")
    def consistent_text(self) -> Self:
        if self.text != normalize_text(self.text):
            raise ValueError("Stored text must already be normalized")
        if self.normalized_text_hash != normalized_text_hash(self.text):
            raise ValueError("Normalized text hash does not match stored UTF-8 text")
        cursor = 0
        for expected_page, marker in enumerate(self.pages, start=1):
            if marker.page != expected_page or marker.start != cursor:
                raise ValueError("Page markers must be ordered, contiguous and one-based")
            if marker.end > len(self.text):
                raise ValueError("Page marker lies outside normalized text")
            page_text = self.text[marker.start : marker.end]
            if marker.normalized_text_hash != normalized_text_hash(page_text):
                raise ValueError("Page hash does not match its normalized text")
            cursor = marker.end
            if expected_page < len(self.pages):
                if self.text[cursor : cursor + len(PAGE_SEPARATOR)] != PAGE_SEPARATOR:
                    raise ValueError("Page separator does not match the recorded boundary")
                cursor += len(PAGE_SEPARATOR)
        if self.pages and cursor != len(self.text):
            raise ValueError("Page markers must cover the entire normalized resource")
        return self

    def page_text(self, page: int | None) -> str:
        """Select the coordinate space; no guessed or silently clamped page IDs."""
        if page is None:
            if self.pages:
                raise ValueError("Paged text requires a page-local citation")
            return self.text
        if type(page) is not int or not 1 <= page <= len(self.pages):
            raise ValueError("Citation page does not exist")
        marker = self.pages[page - 1]
        return self.text[marker.start : marker.end]

    def citation_hash(self, page: int | None) -> str:
        self.page_text(page)
        return (
            self.normalized_text_hash if page is None else self.pages[page - 1].normalized_text_hash
        )

    def slice(self, start: int, end: int, *, page: int | None = None) -> str:
        text = self.page_text(page)
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise ValueError("Citation offsets must be a nonempty in-bounds half-open range")
        return text[start:end]

    def source_span(
        self, span_id: UUID, start: int, end: int, *, page: int | None = None
    ) -> SourceSpan:
        return SourceSpan(
            id=span_id, page=page, start=start, end=end, quote=self.slice(start, end, page=page)
        )

    def validate_span(self, span: SourceSpan | Evidence) -> None:
        """Reject same-length invented quotes as well as invalid coordinate spaces."""
        if self.slice(span.start, span.end, page=span.page) != span.quote:
            raise ValueError("Citation quote does not match the exact normalized text slice")
        if isinstance(span, Evidence) and span.normalized_text_hash != self.citation_hash(
            span.page
        ):
            raise ValueError("Evidence hash does not match the cited normalized page")


def normalize_document(text: str) -> NormalizedText:
    text = normalize_text(text)
    return NormalizedText(
        normalization_version=NORMALIZATION_VERSION,
        text=text,
        normalized_text_hash=normalized_text_hash(text),
        pages=(),
    )


def normalize_pages(pages: Sequence[str]) -> NormalizedText:
    """The parser supplies page order explicitly, including blank pages.

    A form-feed inside extracted text is content; it is never split heuristically
    into pages. Only the marker table establishes page identity.
    """
    if isinstance(pages, str) or not pages:
        raise ValueError("Paged normalization requires a nonempty sequence of page strings")
    normalized = tuple(normalize_text(page) for page in pages)
    markers: list[PageMarker] = []
    cursor = 0
    for page, text in enumerate(normalized, start=1):
        markers.append(
            PageMarker(
                page=page,
                start=cursor,
                end=cursor + len(text),
                normalized_text_hash=normalized_text_hash(text),
            )
        )
        cursor += len(text) + len(PAGE_SEPARATOR)
    text = PAGE_SEPARATOR.join(normalized)
    return NormalizedText(
        normalization_version=NORMALIZATION_VERSION,
        text=text,
        normalized_text_hash=normalized_text_hash(text),
        pages=tuple(markers),
    )


class SourceSnapshot(DomainModel):
    """Reuse MS-002 metadata without promoting authority from a URL or snippet.

    The ingestion adapter supplies the classified Source and raw resource hash.
    This contract validates normalized provenance; resolution, source entailment,
    authorization and currentness remain the responsible services' obligations.
    """

    source: Source = Field(repr=False)
    normalized: NormalizedText = Field(repr=False)
    raw_file_hash: Sha256

    @model_validator(mode="after")
    def bound_source(self) -> Self:
        if self.source.content_hash != self.normalized.normalized_text_hash:
            raise ValueError("Source content_hash must bind the normalized resource")
        for span in self.source.spans:
            self.normalized.validate_span(span)
        return self


class DocumentText(DomainModel):
    """Version-bound private evidence text; identity is supplied by trusted ingestion."""

    document_id: UUID
    document_version_id: UUID
    normalized: NormalizedText = Field(repr=False)
    raw_file_hash: Sha256

    @model_validator(mode="after")
    def require_document_pages(self) -> Self:
        if not self.normalized.pages:
            raise ValueError("Document evidence requires explicit page markers")
        return self

    def evidence(self, span_id: UUID, page: int, start: int, end: int) -> Evidence:
        return Evidence(
            id=span_id,
            document_id=self.document_id,
            document_version_id=self.document_version_id,
            page=page,
            start=start,
            end=end,
            quote=self.normalized.slice(start, end, page=page),
            normalized_text_hash=self.normalized.citation_hash(page),
        )

    def validate_evidence(self, evidence: Evidence) -> None:
        if (
            evidence.document_id != self.document_id
            or evidence.document_version_id != self.document_version_id
        ):
            raise ValueError("Evidence does not belong to the pinned document version")
        self.normalized.validate_span(evidence)
