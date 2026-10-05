"""Versioned benchmark custody metadata; these are not public application DTOs."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from benefitbridge.domain.base import (
    DomainModel,
    HttpsUrl,
    PositiveInt,
    Sha256,
    UtcTimestamp,
)
from benefitbridge.domain.enums import ClaimStatus, Eligibility, Lane

Identifier = Annotated[str, Field(strict=True, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")]
Text = Annotated[str, Field(strict=True, min_length=1, max_length=2000)]


class Split(StrEnum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    TEST = "test"


class Asset(DomainModel):
    """SHA-256 of exact local file bytes, independent of normalized application hashes."""

    path: Text
    content_hash: Sha256


class Permission(DomainModel):
    license: Text
    permission_basis: Text
    permission_reference: Text
    redistribution: Literal["permitted", "restricted"]


class Gold[T](DomainModel):
    """Human custody record only; validation cannot attest annotation correctness."""

    value: T
    annotators: tuple[Identifier, Identifier]
    adjudicator: Identifier
    guide_version: Identifier
    annotated_at: UtcTimestamp
    rationale: Text = Field(repr=False)

    @model_validator(mode="after")
    def independent_review(self) -> "Gold[T]":
        if len(set((*self.annotators, self.adjudicator))) != 3:
            raise ValueError("Two independent annotators and a third adjudicator are required")
        return self


class Record(DomainModel):
    id: Identifier
    version: PositiveInt
    split: Split
    asset: Asset


class Source(Record):
    provider_family: Identifier
    program_family: Identifier
    intake_lineage: Identifier
    policy_template_family: Identifier
    lane: Lane
    origin: Literal["published", "synthetic"]
    provider_name: Text
    url: HttpsUrl | None = None
    retrieved_at: UtcTimestamp
    permission: Permission
    gold: Gold[Asset] | None = None

    @model_validator(mode="after")
    def publication_origin(self) -> "Source":
        if self.origin == "published" and self.url is None:
            raise ValueError("Published sources require an authoritative URL")
        if self.origin == "synthetic" and self.url is not None:
            raise ValueError("Synthetic policies must not claim a published provider URL")
        return self


class Profile(Record):
    origin: Literal["synthetic"]
    profile_family: Identifier
    document_template_family: Identifier
    permission: Permission
    documents: tuple[Asset, ...] = ()
    gold: Gold[Asset] | None = None


class Pair(Record):
    source_id: Identifier
    profile_id: Identifier
    gold: Gold[Eligibility] | None = None


class Relevance(DomainModel):
    source_id: Identifier
    grade: Annotated[int, Field(strict=True, ge=0, le=2)]


class Query(Record):
    lane: Lane
    candidate_source_ids: tuple[Identifier, ...]
    gold: Gold[tuple[Relevance, ...]] | None = None


class Claim(Record):
    pair_id: Identifier
    gold: Gold[ClaimStatus] | None = None


class Manifest(DomainModel):
    schema_version: Literal["1.0.0"]
    benchmark: Literal["BenefitBridge-Bench"]
    provenance: Literal["team-created"]
    dataset_version: Identifier
    reference_time: UtcTimestamp
    frozen_at: UtcTimestamp
    annotation_guide_version: Identifier
    test_label_custodian: Identifier
    sources: tuple[Source, ...]
    profiles: tuple[Profile, ...]
    pairs: tuple[Pair, ...]
    queries: tuple[Query, ...]
    claims: tuple[Claim, ...]
