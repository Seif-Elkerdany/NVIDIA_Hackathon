"""Bounded rule AST integrity, without evaluating applicant eligibility."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, Field, StrictBool, model_validator

from .base import CountryCode, DomainModel, NonEmpty, ShortText, UUIDs, unique_items
from .enums import (
    Applicability,
    Completeness,
    EvidenceExpectation,
    FactAttribute,
    Interpretation,
    Modality,
    Operator,
    ReferenceTime,
    RuleType,
    TaskKind,
)
from .facts import (
    ATTRIBUTE_TYPES,
    CountrySetValue,
    DateValue,
    FactValue,
    GpaValue,
    StringSetValue,
    StringValue,
    UnknownValue,
)

ScalarValue = Annotated[StringValue | GpaValue | DateValue, Field(discriminator="type")]


class IntervalValue(DomainModel):
    type: Literal["INTERVAL"]
    lower: ScalarValue
    upper: ScalarValue
    lower_inclusive: StrictBool
    upper_inclusive: StrictBool

    @model_validator(mode="after")
    def compatible_bounds(self) -> Self:
        if type(self.lower) is not type(self.upper):
            raise ValueError("Interval bounds must have the same value tag")
        if isinstance(self.lower, GpaValue) and isinstance(self.upper, GpaValue):
            if self.lower.scale_max != self.upper.scale_max:
                raise ValueError("Interval GPA bounds must use the same scale")
            lower, upper = self.lower.number, self.upper.number
            if lower > upper or (
                lower == upper and not (self.lower_inclusive and self.upper_inclusive)
            ):
                raise ValueError("Interval must not be reversed or empty")
        if isinstance(self.lower, DateValue) and isinstance(self.upper, DateValue):
            if self.lower.precision == self.upper.precision and self.lower.value > self.upper.value:
                raise ValueError("Date interval must not be reversed")
        return self


ExpectedValue = Annotated[FactValue | IntervalValue, Field(discriminator="type")]


class RuleScope(DomainModel):
    cycle: NonEmpty
    location_countries: Annotated[tuple[CountryCode, ...], AfterValidator(unique_items)]


class AllNode(DomainModel):
    id: NonEmpty
    type: Literal[RuleType.ALL]
    children: Annotated[
        tuple[NonEmpty, ...], Field(min_length=1, max_length=50), AfterValidator(unique_items)
    ]


class AnyNode(DomainModel):
    id: NonEmpty
    type: Literal[RuleType.ANY]
    children: Annotated[
        tuple[NonEmpty, ...], Field(min_length=1, max_length=50), AfterValidator(unique_items)
    ]


class NotNode(DomainModel):
    id: NonEmpty
    type: Literal[RuleType.NOT]
    child: NonEmpty


class PredicateNode(DomainModel):
    id: NonEmpty
    type: Literal[RuleType.PREDICATE]
    modality: Modality
    # Unsupported source attributes remain representable for downstream UNKNOWN handling.
    attribute: NonEmpty
    operator: Operator
    expected: ExpectedValue
    source_span_ids: Annotated[UUIDs, Field(min_length=1)]
    scope: RuleScope
    reference_time: ReferenceTime
    reference_date: DateValue | None = Field(default=None, exclude_if=lambda value: value is None)
    interpretation: Interpretation
    evidence_expectation: EvidenceExpectation

    @model_validator(mode="after")
    def valid_predicate(self) -> Self:
        if self.reference_time == ReferenceTime.EXPLICIT:
            if self.reference_date is None:
                raise ValueError("EXPLICIT reference time requires a reference_date")
        elif "reference_date" in self.model_fields_set:
            raise ValueError("Omit reference_date unless reference_time is EXPLICIT")
        expected = self.expected
        if self.operator in {Operator.IN, Operator.NOT_IN}:
            if not isinstance(expected, (CountrySetValue, StringSetValue, UnknownValue)):
                raise ValueError("Membership operators require a typed set")
        if self.operator in {Operator.BEFORE, Operator.AFTER}:
            if not isinstance(expected, (DateValue, UnknownValue)):
                raise ValueError("Date operators require a typed date")
        if self.attribute in FactAttribute._value2member_map_ and not isinstance(
            expected, UnknownValue
        ):
            kind = ATTRIBUTE_TYPES[FactAttribute(self.attribute)]
            if isinstance(expected, IntervalValue):
                if not isinstance(expected.lower, kind):
                    raise ValueError("Interval tag does not match the known attribute")
            elif self.operator in {Operator.IN, Operator.NOT_IN} and kind is StringValue:
                if not isinstance(expected, StringSetValue):
                    raise ValueError("String membership requires STRING_SET")
            elif not isinstance(expected, kind):
                raise ValueError("Predicate value tag does not match the known attribute")
        return self


RuleNode = Annotated[AllNode | AnyNode | NotNode | PredicateNode, Field(discriminator="type")]


class ApplicationTask(DomainModel):
    key: NonEmpty
    label: NonEmpty
    required: StrictBool
    kind: TaskKind
    applicability: Applicability
    source_span_ids: Annotated[UUIDs, Field(min_length=1)]


def child_ids(node: RuleNode) -> tuple[str, ...]:
    if isinstance(node, (AllNode, AnyNode)):
        return node.children
    if isinstance(node, NotNode):
        return (node.child,)
    return ()


class RequirementSet(DomainModel):
    id: UUID
    opportunity_version_id: UUID
    schema_version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    completeness: Completeness
    mandatory_root: NonEmpty | None
    preferred_roots: Annotated[tuple[NonEmpty, ...], AfterValidator(unique_items)]
    nodes: Annotated[tuple[RuleNode, ...], Field(max_length=100)]
    application_tasks: tuple[ApplicationTask, ...]
    issues: tuple[ShortText, ...]

    @model_validator(mode="after")
    def valid_graph(self) -> Self:
        nodes = {node.id: node for node in self.nodes}
        if len(nodes) != len(self.nodes):
            raise ValueError("Rule node IDs must be unique")
        roots = self.preferred_roots + ((self.mandatory_root,) if self.mandatory_root else ())
        if any(root not in nodes for root in roots):
            raise ValueError("Rule root refers to a missing node")
        if self.mandatory_root in self.preferred_roots:
            raise ValueError("Mandatory and preferred roots must be distinct")
        if len({task.key for task in self.application_tasks}) != len(self.application_tasks):
            raise ValueError("Application task keys must be unique")
        visiting: set[str] = set()
        heights: dict[str, int] = {}

        def height(node_id: str) -> int:
            if node_id not in nodes:
                raise ValueError("Rule child refers to a missing node")
            if node_id in visiting:
                raise ValueError("Rule graph contains a cycle")
            if node_id in heights:
                return heights[node_id]
            visiting.add(node_id)
            depth = 1 + max((height(child) for child in child_ids(nodes[node_id])), default=0)
            visiting.remove(node_id)
            if depth > 12:
                raise ValueError("Rule graph exceeds maximum depth 12")
            heights[node_id] = depth
            return depth

        # Check disconnected nodes too: an unused cycle is still untrusted invalid input.
        for node in self.nodes:
            height(node.id)

        def check_modality(root: str, excluded: set[Modality]) -> None:
            pending, seen = [root], set()
            while pending:
                node_id = pending.pop()
                if node_id in seen:
                    continue
                seen.add(node_id)
                node = nodes[node_id]
                if isinstance(node, PredicateNode) and node.modality in excluded:
                    raise ValueError("Rule root contains an incompatible requirement modality")
                pending.extend(child_ids(node))

        if self.mandatory_root is not None:
            check_modality(self.mandatory_root, {Modality.PREFERRED, Modality.OPTIONAL})
        for root in self.preferred_roots:
            check_modality(root, {Modality.MANDATORY, Modality.OPTIONAL})
        return self


def validate_source_references(
    requirements: RequirementSet, source_span_ids: frozenset[UUID]
) -> None:
    """Validate against the caller's pinned source bundle before publication.

    This proves membership only. Source adapters/verification own quote entailment,
    normalized text matching, authorization and currentness.
    """
    references = {
        span_id
        for node in requirements.nodes
        if isinstance(node, PredicateNode)
        for span_id in node.source_span_ids
    }
    references.update(
        span_id for task in requirements.application_tasks for span_id in task.source_span_ids
    )
    if not references <= source_span_ids:
        raise ValueError("Requirement references a span outside the pinned source bundle")
