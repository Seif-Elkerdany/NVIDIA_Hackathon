"""Request payloads from API.md. Authorization and currentness belong to services."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, BeforeValidator, Field, StrictBool, StrictStr, model_validator

from .base import (
    CountryCode,
    DomainModel,
    HttpsUrl,
    NonEmpty,
    PositiveInt,
    Sha256,
    ShortText,
    StatementText,
    TimezoneName,
    UUIDs,
    WatchInterval,
    unique_items,
)
from .enums import ChecklistStatus, DemoScenario, DocumentKind, FactAttribute, Lane, ReviewAction
from .facts import FactInput, FactValue


class EmptyCommand(DomainModel):
    """The documented empty JSON payload, distinct from endpoints with no body."""


class PatchMe(DomainModel):
    display_name: ShortText | None = Field(default=None, exclude_if=lambda value: value is None)
    timezone: TimezoneName | None = Field(default=None, exclude_if=lambda value: value is None)
    consent_version: NonEmpty | None = Field(default=None, exclude_if=lambda value: value is None)

    @model_validator(mode="after")
    def nonempty_patch(self) -> Self:
        if not self.model_fields_set or any(
            getattr(self, name) is None for name in self.model_fields_set
        ):
            raise ValueError("Provide at least one non-null account patch field")
        return self


class PatchProfile(DomainModel):
    base_profile_version_id: UUID
    changes: Annotated[tuple[FactInput, ...], Field(max_length=100)]
    remove_attributes: Annotated[
        tuple[FactAttribute, ...], Field(max_length=100), AfterValidator(unique_items)
    ]

    @model_validator(mode="after")
    def distinct_changes(self) -> Self:
        count = len(self.changes) + len(self.remove_attributes)
        changed = {change.attribute for change in self.changes}
        if not 1 <= count <= 100:
            raise ValueError("Profile patch requires 1 to 100 total changes and removals")
        if len(changed) != len(self.changes) or changed.intersection(self.remove_attributes):
            raise ValueError("Attributes cannot be repeated or both changed and removed")
        return self


class CreateDocumentUpload(DomainModel):
    filename: Annotated[StrictStr, Field(min_length=1, max_length=120)]
    kind: DocumentKind
    content_type: Literal["application/pdf"]
    size_bytes: Annotated[PositiveInt, Field(le=10 * 1024 * 1024)]
    sha256: Sha256

    @model_validator(mode="after")
    def filename_is_basename(self) -> Self:
        if self.filename in {".", ".."} or any(c in self.filename for c in "/\\:\x00"):
            raise ValueError("Filename must be a basename, never a path")
        return self


class CompleteDocumentUpload(DomainModel):
    sha256: Sha256


class AcceptCandidate(DomainModel):
    candidate_id: UUID
    action: Literal[ReviewAction.ACCEPT]


class RejectCandidate(DomainModel):
    candidate_id: UUID
    action: Literal[ReviewAction.REJECT]


class CorrectCandidate(DomainModel):
    candidate_id: UUID
    action: Literal[ReviewAction.CORRECT]
    value: FactValue
    explanation: Annotated[StrictStr, Field(min_length=1, max_length=500)]


CandidateDecision = Annotated[
    AcceptCandidate | RejectCandidate | CorrectCandidate, Field(discriminator="action")
]


class ReviewFactCandidates(DomainModel):
    base_profile_version_id: UUID
    decisions: Annotated[tuple[CandidateDecision, ...], Field(min_length=1, max_length=50)]

    @model_validator(mode="after")
    def unique_candidates(self) -> Self:
        if len({decision.candidate_id for decision in self.decisions}) != len(self.decisions):
            raise ValueError("Each candidate must be reviewed exactly once")
        return self


class DiscoveryPreferences(DomainModel):
    countries: Annotated[
        tuple[CountryCode, ...], Field(max_length=10), AfterValidator(unique_items)
    ]
    remote: StrictBool | None
    fields: Annotated[tuple[ShortText, ...], Field(max_length=10), AfterValidator(unique_items)]
    funding_required: StrictBool | None


class StartDiscovery(DomainModel):
    profile_version_id: UUID
    goal: Annotated[StrictStr, Field(min_length=20, max_length=1000)]
    lane: Lane
    preferences: DiscoveryPreferences


class ImportOpportunity(DomainModel):
    profile_version_id: UUID
    url: Annotated[HttpsUrl, Field(max_length=2048)]


class ClarificationAnswer(DomainModel):
    question_id: NonEmpty
    value: FactValue | None
    skip: StrictBool

    @model_validator(mode="after")
    def explicit_skip(self) -> Self:
        if self.skip != (self.value is None):
            raise ValueError("Skipping requires null value; answering requires a typed value")
        return self


class AnswerClarifications(DomainModel):
    revision: PositiveInt
    base_profile_version_id: UUID
    answers: Annotated[tuple[ClarificationAnswer, ...], Field(max_length=3)]

    @model_validator(mode="after")
    def unique_answers(self) -> Self:
        if len({answer.question_id for answer in self.answers}) != len(self.answers):
            raise ValueError("Each clarification question must be answered exactly once")
        return self


class StartEvaluation(DomainModel):
    opportunity_version_id: UUID
    profile_version_id: UUID


class CreateApplication(DomainModel):
    evaluation_id: UUID
    replace_stale: StrictBool


class PatchChecklistItem(DomainModel):
    base_revision: PositiveInt
    status: ChecklistStatus
    evidence_ids: Annotated[UUIDs, Field(max_length=10)]


class StartDraft(DomainModel):
    base_revision: PositiveInt
    target_words: Annotated[PositiveInt, Field(ge=150, le=500)]


class EditDraft(DomainModel):
    base_application_revision: PositiveInt
    text: StatementText


def confirmed_true(value: object) -> Literal[True]:
    if value is not True:
        raise ValueError("Confirmation must be JSON true")
    return True


class AcceptDraft(DomainModel):
    base_application_revision: PositiveInt
    confirmed_review: Annotated[Literal[True], BeforeValidator(confirmed_true)]


class DeleteAccount(DomainModel):
    confirmation: Literal["DELETE"]


class ResetDemo(DomainModel):
    scenario: DemoScenario


class CreateWatch(DomainModel):
    opportunity_id: UUID
    interval_hours: WatchInterval


class PatchWatch(DomainModel):
    base_revision: PositiveInt
    enabled: StrictBool | None = Field(default=None, exclude_if=lambda value: value is None)
    interval_hours: WatchInterval | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def nonempty_patch(self) -> Self:
        supplied = self.model_fields_set - {"base_revision"}
        if not supplied or any(getattr(self, name) is None for name in supplied):
            raise ValueError("Provide enabled or interval_hours with a non-null value")
        return self
