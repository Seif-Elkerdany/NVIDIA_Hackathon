"""API.md response DTO catalog and common envelopes; all snapshots are immutable."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, Field, StrictBool, StrictFloat, StrictStr, model_validator

from .base import (
    CountryCode,
    DomainModel,
    HttpsUrl,
    NonEmpty,
    NonNegativeInt,
    PositiveInt,
    Sha256,
    ShortText,
    StatementText,
    TimezoneName,
    UtcTimestamp,
    UUIDs,
    WatchInterval,
    unique_items,
    validate_partial_date,
)
from .enums import (
    AccountStatus,
    Applicability,
    ApplicationState,
    ArtifactType,
    Authority,
    Availability,
    ChecklistStatus,
    ClaimStatus,
    Completeness,
    Currentness,
    DeadlinePrecision,
    DeletionStatus,
    DocumentKind,
    DocumentQuality,
    DocumentStatus,
    DraftValidation,
    Eligibility,
    EvaluationMethod,
    EvaluationState,
    FactAttribute,
    FactType,
    FreshnessState,
    Lane,
    NotificationKind,
    ReasonCode,
    RunKind,
    RunStatus,
    TaskKind,
    Truth,
)
from .facts import ATTRIBUTE_TYPES, Fact

UnitFraction = Annotated[StrictFloat, Field(ge=0, le=1)]
Percent = Annotated[NonNegativeInt, Field(le=100)]


class Envelope[T](DomainModel):
    data: T
    request_id: Annotated[StrictStr, Field(min_length=1, max_length=64)]


class Page[T](DomainModel):
    items: Annotated[tuple[T, ...], Field(max_length=100)]
    next_cursor: NonEmpty | None


class FieldError(DomainModel):
    path: NonEmpty
    message: NonEmpty


class Problem(DomainModel):
    type: Annotated[StrictStr, Field(pattern=r"^urn:benefitbridge:problem:[a-z0-9-]+$")]
    title: NonEmpty
    status: Annotated[NonNegativeInt, Field(ge=400, le=599)]
    detail: NonEmpty
    # Endpoint-specific code families are explicitly extensible in API.md.
    code: Annotated[StrictStr, Field(pattern=r"^[A-Z][A-Z0-9_]*$")]
    request_id: Annotated[StrictStr, Field(min_length=1, max_length=64)]
    errors: tuple[FieldError, ...]
    retryable: StrictBool


class Consent(DomainModel):
    version: NonEmpty
    accepted_at: UtcTimestamp


class Account(DomainModel):
    id: UUID
    display_name: ShortText
    timezone: TimezoneName
    status: AccountStatus
    consent: Consent | None
    is_demo: StrictBool
    created_at: UtcTimestamp


class Profile(DomainModel):
    id: UUID
    version_id: UUID
    version_number: PositiveInt
    facts: Annotated[tuple[Fact, ...], Field(max_length=100)]
    updated_at: UtcTimestamp

    @model_validator(mode="after")
    def unique_facts(self) -> Self:
        if len({fact.id for fact in self.facts}) != len(self.facts):
            raise ValueError("Profile fact IDs must be unique")
        if len({fact.attribute for fact in self.facts}) != len(self.facts):
            raise ValueError("Profile must contain at most one fact per attribute")
        return self


class Document(DomainModel):
    id: UUID
    filename: Annotated[StrictStr, Field(min_length=1, max_length=120)]
    kind: DocumentKind
    status: DocumentStatus
    size_bytes: NonNegativeInt
    sha256: Sha256
    version_id: UUID | None
    page_count: PositiveInt | None
    quality: DocumentQuality | None
    failure_code: NonEmpty | None
    created_at: UtcTimestamp
    deleted_at: UtcTimestamp | None


class Evidence(DomainModel):
    id: UUID
    document_id: UUID
    document_version_id: UUID
    page: PositiveInt
    start: NonNegativeInt
    end: NonNegativeInt
    quote: NonEmpty
    normalized_text_hash: Sha256

    @model_validator(mode="after")
    def exact_span_length(self) -> Self:
        if self.end - self.start != len(self.quote):
            raise ValueError("Evidence quote length must equal end minus start in code points")
        return self


class RunReceipt(DomainModel):
    run_id: UUID
    status: Literal[RunStatus.QUEUED]
    status_url: NonEmpty
    events_url: NonEmpty

    @model_validator(mode="after")
    def matching_urls(self) -> Self:
        path = f"/api/v1/runs/{self.run_id}"
        if self.status_url != path or self.events_url != path + "/events":
            raise ValueError("Run receipt URLs must reference the received run")
        return self


class RunProgress(DomainModel):
    completed_units: NonNegativeInt
    total_units: NonNegativeInt | None

    @model_validator(mode="after")
    def bounded_progress(self) -> Self:
        if self.total_units is not None and self.completed_units > self.total_units:
            raise ValueError("Completed progress cannot exceed known total")
        return self


class RunFunnel(DomainModel):
    raw_hits: NonNegativeInt
    canonical: NonNegativeInt
    official: NonNegativeInt
    parsed: NonNegativeInt
    evaluated: NonNegativeInt


class RunResultRefs(DomainModel):
    opportunity_ids: UUIDs
    evaluation_ids: UUIDs
    draft_ids: UUIDs


class Run(DomainModel):
    id: UUID
    kind: RunKind
    status: RunStatus
    # Stages differ by workflow; API.md does not define a closed cross-workflow enum.
    stage: NonEmpty
    profile_version_id: UUID | None
    cancel_requested: StrictBool
    progress: RunProgress
    funnel: RunFunnel
    result_refs: RunResultRefs
    warnings: tuple[NonEmpty, ...]
    failure_code: NonEmpty | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp


class Deadline(DomainModel):
    raw_text: StrictStr
    precision: DeadlinePrecision
    date: StrictStr | None
    at: UtcTimestamp | None
    timezone: TimezoneName | None
    ambiguity: NonEmpty | None

    @model_validator(mode="after")
    def matching_representation(self) -> Self:
        if self.precision == DeadlinePrecision.INSTANT:
            if self.at is None or self.date is not None:
                raise ValueError("INSTANT requires at and forbids a date representation")
        elif self.precision == DeadlinePrecision.UNKNOWN:
            if self.at is not None or self.date is not None:
                raise ValueError("UNKNOWN deadline cannot imply a date or instant")
        else:
            if self.date is None or self.at is not None:
                raise ValueError("Date-precision deadlines require date and forbid at")
            precision = "DAY" if self.precision == DeadlinePrecision.DATE else self.precision.value
            validate_partial_date(self.date, precision)
        return self


class Freshness(DomainModel):
    state: FreshnessState
    checked_at: UtcTimestamp
    expires_at: UtcTimestamp


class Opportunity(DomainModel):
    id: UUID
    version_id: UUID
    title: NonEmpty
    provider: NonEmpty
    lane: Lane
    cycle: NonEmpty
    location_countries: Annotated[tuple[CountryCode, ...], AfterValidator(unique_items)]
    remote: StrictBool
    official_url: HttpsUrl
    authority: Authority
    availability: Availability
    deadline: Deadline
    freshness: Freshness
    requirement_set_id: UUID
    evaluation_id: UUID | None
    evaluation_state: EvaluationState

    @model_validator(mode="after")
    def evaluation_reference(self) -> Self:
        if (self.evaluation_id is None) != (self.evaluation_state == EvaluationState.NOT_EVALUATED):
            raise ValueError("Evaluation reference must agree with evaluation_state")
        return self


class SourceSpan(DomainModel):
    id: UUID
    page: PositiveInt | None
    start: NonNegativeInt
    end: NonNegativeInt
    quote: NonEmpty

    @model_validator(mode="after")
    def exact_span_length(self) -> Self:
        if self.end - self.start != len(self.quote):
            raise ValueError("Source quote length must equal end minus start in code points")
        return self


class Source(DomainModel):
    id: UUID
    url: HttpsUrl
    snapshot_id: UUID
    retrieved_at: UtcTimestamp
    content_hash: Sha256
    authority: Authority
    completeness: Completeness
    spans: tuple[SourceSpan, ...]

    @model_validator(mode="after")
    def unique_spans(self) -> Self:
        if len({span.id for span in self.spans}) != len(self.spans):
            raise ValueError("Source span IDs must be unique")
        return self


class FitComponent(DomainModel):
    name: NonEmpty
    weight: UnitFraction
    value: UnitFraction | None


class Fit(DomainModel):
    score: Percent | None
    coverage: UnitFraction
    components: tuple[FitComponent, ...]

    @model_validator(mode="after")
    def reconciled_components(self) -> Self:
        if len({part.name for part in self.components}) != len(self.components):
            raise ValueError("Fit component names must be unique")
        total = sum((Decimal(str(part.weight)) for part in self.components), Decimal(0))
        if self.components and abs(total - 1) > Decimal("1e-9"):
            raise ValueError("Fit weights must be normalized")
        known = [part for part in self.components if part.value is not None]
        coverage = sum((Decimal(str(part.weight)) for part in known), Decimal(0))
        if abs(coverage - Decimal(str(self.coverage))) > Decimal("1e-9"):
            raise ValueError("Fit coverage must equal the weight of known components")
        score = None
        if coverage:
            weighted = sum(
                (Decimal(str(part.weight)) * Decimal(str(part.value)) for part in known), Decimal(0)
            )
            score = int((100 * weighted / coverage).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        if self.score != score:
            raise ValueError("Fit score must reconcile with its known components")
        return self


class Readiness(DomainModel):
    completed: NonNegativeInt
    required: NonNegativeInt
    percent: Percent | None
    unknown_applicability: NonNegativeInt

    @model_validator(mode="after")
    def reconciled_counts(self) -> Self:
        if self.completed > self.required:
            raise ValueError("Completed required tasks cannot exceed required tasks")
        percent = None
        if self.required and not self.unknown_applicability:
            percent = int(
                (Decimal(100) * self.completed / self.required).quantize(
                    Decimal(1), rounding=ROUND_HALF_UP
                )
            )
        if self.percent != percent:
            raise ValueError(
                "Readiness percent must reconcile with counts and unknown applicability"
            )
        return self


class LeafResult(DomainModel):
    node_id: NonEmpty
    truth: Truth
    method: EvaluationMethod
    fact_ids: UUIDs
    evidence_ids: UUIDs
    source_span_ids: UUIDs
    reason_codes: tuple[ReasonCode, ...]
    explanation: NonEmpty


class EvaluationVersions(DomainModel):
    evaluator: NonEmpty
    prompts: NonEmpty
    registry: NonEmpty
    freshness: NonEmpty


class Evaluation(DomainModel):
    id: UUID
    opportunity_id: UUID
    opportunity_version_id: UUID
    profile_version_id: UUID
    requirement_set_id: UUID
    eligibility: Eligibility
    availability: Availability
    fit: Fit
    readiness: Readiness
    currentness: Currentness
    reason_codes: tuple[ReasonCode, ...]
    leaves: tuple[LeafResult, ...]
    as_of: UtcTimestamp
    valid_until: UtcTimestamp
    versions: EvaluationVersions

    @model_validator(mode="after")
    def unique_leaves(self) -> Self:
        if len({leaf.node_id for leaf in self.leaves}) != len(self.leaves):
            raise ValueError("Evaluation leaf node IDs must be unique")
        return self


class ClarificationQuestion(DomainModel):
    id: NonEmpty
    attribute: FactAttribute
    prompt: NonEmpty
    value_type: FactType
    reason: NonEmpty
    required_for_nodes: Annotated[
        tuple[NonEmpty, ...], Field(min_length=1), AfterValidator(unique_items)
    ]

    @model_validator(mode="after")
    def matching_value_type(self) -> Self:
        schema = ATTRIBUTE_TYPES[self.attribute].model_json_schema()
        if self.value_type != schema["properties"]["type"]["const"]:
            raise ValueError("Question value_type must match the fact attribute")
        return self


class ClarificationSet(DomainModel):
    id: UUID
    run_id: UUID
    revision: PositiveInt
    round: Annotated[PositiveInt, Field(le=2)]
    base_profile_version_id: UUID
    questions: Annotated[tuple[ClarificationQuestion, ...], Field(max_length=3)]
    expires_at: UtcTimestamp

    @model_validator(mode="after")
    def unique_questions(self) -> Self:
        if len({question.id for question in self.questions}) != len(self.questions):
            raise ValueError("Question IDs must be unique")
        return self


class Saved(DomainModel):
    opportunity_id: UUID
    saved_at: UtcTimestamp
    current_evaluation_id: UUID | None
    evaluation_state: EvaluationState


class ChecklistItem(DomainModel):
    id: UUID
    key: NonEmpty
    label: NonEmpty
    kind: TaskKind
    required: StrictBool
    applicability: Applicability
    status: ChecklistStatus
    evidence_ids: UUIDs
    draft_id: UUID | None


class Application(DomainModel):
    id: UUID
    opportunity_id: UUID
    opportunity_version_id: UUID
    profile_version_id: UUID
    evaluation_id: UUID
    revision: PositiveInt
    state: ApplicationState
    items: tuple[ChecklistItem, ...]
    readiness: Readiness
    latest_draft_id: UUID | None
    accepted_draft_id: UUID | None
    created_at: UtcTimestamp

    @model_validator(mode="after")
    def unique_items(self) -> Self:
        if len({item.id for item in self.items}) != len(self.items) or len(
            {item.key for item in self.items}
        ) != len(self.items):
            raise ValueError("Checklist IDs and keys must be unique")
        return self


class DraftClaim(DomainModel):
    id: NonEmpty
    start: NonNegativeInt
    end: NonNegativeInt
    text: NonEmpty
    fact_ids: UUIDs
    evidence_ids: UUIDs
    status: ClaimStatus


class Draft(DomainModel):
    id: UUID
    application_id: UUID
    version_number: PositiveInt
    profile_version_id: UUID
    opportunity_version_id: UUID
    text: StatementText
    validation: DraftValidation
    claims: tuple[DraftClaim, ...]
    issues: tuple[NonEmpty, ...]
    accepted_at: UtcTimestamp | None
    created_at: UtcTimestamp

    @model_validator(mode="after")
    def valid_claim_spans(self) -> Self:
        if len({claim.id for claim in self.claims}) != len(self.claims):
            raise ValueError("Draft claim IDs must be unique")
        for claim in self.claims:
            if claim.end > len(self.text) or self.text[claim.start : claim.end] != claim.text:
                raise ValueError("Draft claim must match the exact code-point text slice")
        return self


class Watch(DomainModel):
    id: UUID
    opportunity_id: UUID
    revision: PositiveInt
    enabled: StrictBool
    interval_hours: WatchInterval
    next_due_at: UtcTimestamp


class Notification(DomainModel):
    id: UUID
    watch_id: UUID
    opportunity_id: UUID
    opportunity_version_id: UUID
    kind: NotificationKind
    summary: NonEmpty
    read_at: UtcTimestamp | None
    created_at: UtcTimestamp


class Usage(DomainModel):
    period_start: UtcTimestamp
    period_end: UtcTimestamp
    currency: Literal["USD"]
    spent_microusd: NonNegativeInt
    reserved_microusd: NonNegativeInt
    limit_microusd: NonNegativeInt
    active_runs: NonNegativeInt
    active_run_limit: NonNegativeInt


class Capabilities(DomainModel):
    api_version: Literal["1"]
    watch: StrictBool
    demo_reset: StrictBool
    supported_lanes: Annotated[tuple[Lane, ...], AfterValidator(unique_items)]
    supported_document_types: tuple[Literal["application/pdf"], ...]
    max_document_bytes: PositiveInt
    max_document_pages: PositiveInt
    inference_available: StrictBool
    deep_available: StrictBool


class UploadIntent(DomainModel):
    document_id: UUID
    upload_url: NonEmpty
    upload_method: Literal["PUT"]
    expires_at: UtcTimestamp
    max_bytes: PositiveInt


class DocumentDownload(DomainModel):
    url: HttpsUrl
    expires_at: UtcTimestamp


class DeletionAccepted(DomainModel):
    receipt_id: UUID
    receipt_token: NonEmpty
    receipt_url: NonEmpty
    status: Literal[DeletionStatus.PENDING]
    expires_at: UtcTimestamp


class DeletionReceipt(DomainModel):
    id: UUID
    status: DeletionStatus
    requested_at: UtcTimestamp
    active_store_deleted_at: UtcTimestamp | None
    backup_retention_until: UtcTimestamp | None


class HealthLive(DomainModel):
    status: Literal["ok"]


class HealthReady(DomainModel):
    status: Literal["ready"]


class ArtifactRef(DomainModel):
    type: ArtifactType
    id: UUID


class RunEvent(DomainModel):
    run_id: UUID
    seq: NonNegativeInt
    stage: NonEmpty
    status: RunStatus
    message_code: NonEmpty
    artifact_ref: ArtifactRef | None
    at: UtcTimestamp


class DraftEditReceipt(DomainModel):
    draft: Draft
    validation_run: RunReceipt
