"""Pure predicates for R02.02/R06.05/R07.02; graph aggregation belongs to MS-023.

``evaluate_predicate`` consumes the shared AST/fact and returns a shared LeafResult.
Standalone Decimal, GPA, date, deadline and experience helpers are internal ports
for dependent evaluators. Dates are possible calendar intervals, never invented
midnight timestamps. Experience durations use half-open [start, end) intervals,
with an ongoing end clipped to the explicit reference date. No ambient clock,
scale conversion, category synonym, month length or full-time equivalence is used.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from benefitbridge.domain.dto import Deadline, LeafResult
from benefitbridge.domain.enums import (
    DatePrecision,
    DeadlinePrecision,
    EvaluationMethod,
    EvidenceExpectation,
    FactAttribute,
    Interpretation,
    Operator,
    ReasonCode,
    ReferenceTime,
    Truth,
)
from benefitbridge.domain.facts import (
    BooleanValue,
    CountrySetValue,
    DateValue,
    ExperienceValue,
    Fact,
    FactValue,
    GpaValue,
    StringSetValue,
    StringValue,
    UnknownValue,
)
from benefitbridge.domain.rules import ExpectedValue, IntervalValue, PredicateNode


@dataclass(frozen=True)
class PredicateResult:
    truth: Truth
    reason_codes: tuple[ReasonCode, ...] = ()
    explanation: str = "The explicit values were compared deterministically."


def _unknown(code: ReasonCode, explanation: str) -> PredicateResult:
    return PredicateResult(Truth.UNKNOWN, (code,), explanation)


def _known(value: bool) -> PredicateResult:
    return PredicateResult(Truth.TRUE if value else Truth.FALSE)


def _unsupported() -> PredicateResult:
    return _unknown(
        ReasonCode.UNSUPPORTED_RULE,
        "This comparison has no supported deterministic interpretation.",
    )


def _invert(result: PredicateResult) -> PredicateResult:
    if result.truth == Truth.UNKNOWN:
        return result
    return _known(result.truth == Truth.FALSE)


def compare_decimal(
    actual: Decimal | None, expected: Decimal | None, operator: Operator
) -> PredicateResult:
    if actual is None:
        return _unknown(ReasonCode.MISSING_PROFILE_FACT, "The numerical fact is unknown.")
    if (
        not isinstance(actual, Decimal)
        or not isinstance(expected, Decimal)
        or not actual.is_finite()
        or not expected.is_finite()
    ):
        return _unsupported()
    match operator:
        case Operator.EQ:
            return _known(actual == expected)
        case Operator.NE:
            return _known(actual != expected)
        case Operator.GT:
            return _known(actual > expected)
        case Operator.GTE:
            return _known(actual >= expected)
        case Operator.LT:
            return _known(actual < expected)
        case Operator.LTE:
            return _known(actual <= expected)
        case _:
            return _unsupported()


def compare_gpa(
    actual: GpaValue | None, expected: GpaValue | None, operator: Operator
) -> PredicateResult:
    if actual is None or expected is None or actual.scale_max != expected.scale_max:
        return _unknown(
            ReasonCode.INCOMPATIBLE_SCALE,
            "GPA comparison requires both original, compatible scales.",
        )
    return compare_decimal(actual.number, expected.number, operator)


@dataclass(frozen=True)
class DateBounds:
    lower: date
    upper: date


def date_bounds(value: DateValue) -> DateBounds:
    if value.precision == DatePrecision.DAY:
        day = date.fromisoformat(value.value)
        return DateBounds(day, day)
    if value.precision == DatePrecision.MONTH:
        year, month = (int(part) for part in value.value.split("-"))
        return DateBounds(date(year, month, 1), date(year, month, monthrange(year, month)[1]))
    year = int(value.value)
    return DateBounds(date(year, 1, 1), date(year, 12, 31))


def _compare_dates(actual: DateBounds, expected: DateBounds, operator: Operator) -> PredicateResult:
    if operator == Operator.NE:
        return _invert(_compare_dates(actual, expected, Operator.EQ))
    if operator in {Operator.GT, Operator.GTE, Operator.AFTER}:
        reverse = Operator.LTE if operator == Operator.GTE else Operator.LT
        return _compare_dates(expected, actual, reverse)
    if operator == Operator.EQ:
        if actual.lower == actual.upper == expected.lower == expected.upper:
            return _known(True)
        if actual.upper < expected.lower or expected.upper < actual.lower:
            return _known(False)
    elif operator in {Operator.LT, Operator.BEFORE}:
        if actual.upper < expected.lower:
            return _known(True)
        if actual.lower >= expected.upper:
            return _known(False)
    elif operator == Operator.LTE:
        if actual.upper <= expected.lower:
            return _known(True)
        if actual.lower > expected.upper:
            return _known(False)
    else:
        return _unsupported()
    return _unknown(
        ReasonCode.DATE_PRECISION_INSUFFICIENT,
        "Recorded date precision permits different comparison outcomes.",
    )


def compare_dates(actual: DateValue, expected: DateValue, operator: Operator) -> PredicateResult:
    return _compare_dates(date_bounds(actual), date_bounds(expected), operator)


def compare_deadline(moment: datetime, deadline: Deadline, operator: Operator) -> PredicateResult:
    """Compare an aware instant without turning a date-only cutoff into midnight.

    Same-date cutoffs remain uncertain even with an explicit timezone. An IANA
    timezone is needed to compare calendar cutoffs; unavailable timezone data
    remains UNKNOWN. No applicant location is used as a substitute timezone.
    """
    if deadline.ambiguity:
        return _unknown(ReasonCode.AMBIGUOUS_POLICY, "The source deadline is ambiguous.")
    if moment.utcoffset() is None or deadline.precision == DeadlinePrecision.UNKNOWN:
        return _unknown(
            ReasonCode.DATE_PRECISION_INSUFFICIENT,
            "An explicit instant and supported deadline precision are required.",
        )
    if deadline.precision == DeadlinePrecision.INSTANT:
        if deadline.at is None:
            return _unsupported()
        match operator:
            case Operator.LT | Operator.BEFORE:
                return _known(moment < deadline.at)
            case Operator.LTE:
                return _known(moment <= deadline.at)
            case Operator.GT | Operator.AFTER:
                return _known(moment > deadline.at)
            case Operator.GTE:
                return _known(moment >= deadline.at)
            case Operator.EQ:
                return _known(moment == deadline.at)
            case Operator.NE:
                return _known(moment != deadline.at)
            case _:
                return _unsupported()
    if deadline.timezone is None or deadline.date is None:
        return _unknown(
            ReasonCode.DATE_PRECISION_INSUFFICIENT,
            "A calendar deadline requires its published timezone.",
        )
    try:
        local_day = moment.astimezone(ZoneInfo(deadline.timezone)).date()
    except ZoneInfoNotFoundError:
        return _unknown(
            ReasonCode.DATE_PRECISION_INSUFFICIENT, "The published timezone cannot be resolved."
        )
    precision = (
        DatePrecision.DAY
        if deadline.precision == DeadlinePrecision.DATE
        else DatePrecision(deadline.precision.value)
    )
    bounds = date_bounds(
        DateValue(type="DATE", value=deadline.date, precision=precision, expected=False)
    )
    if operator not in {
        Operator.EQ,
        Operator.NE,
        Operator.LT,
        Operator.LTE,
        Operator.BEFORE,
        Operator.GT,
        Operator.GTE,
        Operator.AFTER,
    }:
        return _unsupported()
    if bounds.lower <= local_day <= bounds.upper:
        return _unknown(
            ReasonCode.DATE_PRECISION_INSUFFICIENT,
            "The date-only deadline does not specify a cutoff instant.",
        )
    return _compare_dates(DateBounds(local_day, local_day), bounds, operator)


def _interval(actual: FactValue, expected: IntervalValue) -> PredicateResult:
    if (
        isinstance(actual, GpaValue)
        and isinstance(expected.lower, GpaValue)
        and isinstance(expected.upper, GpaValue)
    ):
        if actual.scale_max != expected.lower.scale_max:
            return _unknown(
                ReasonCode.INCOMPATIBLE_SCALE, "GPA interval requires the same original scale."
            )
        low = (
            actual.number >= expected.lower.number
            if expected.lower_inclusive
            else actual.number > expected.lower.number
        )
        high = (
            actual.number <= expected.upper.number
            if expected.upper_inclusive
            else actual.number < expected.upper.number
        )
        return _known(low and high)
    if (
        isinstance(actual, DateValue)
        and isinstance(expected.lower, DateValue)
        and isinstance(expected.upper, DateValue)
    ):
        value, lower, upper = (
            date_bounds(actual),
            date_bounds(expected.lower),
            date_bounds(expected.upper),
        )
        low_offset, high_offset = (
            int(not expected.lower_inclusive),
            int(not expected.upper_inclusive),
        )
        if lower.upper.toordinal() + low_offset > upper.lower.toordinal() - high_offset:
            return _unknown(
                ReasonCode.AMBIGUOUS_POLICY, "The interval bounds may be reversed or empty."
            )
        if (
            value.lower.toordinal() >= lower.upper.toordinal() + low_offset
            and value.upper.toordinal() <= upper.lower.toordinal() - high_offset
        ):
            return _known(True)
        if (
            value.upper.toordinal() < lower.lower.toordinal() + low_offset
            or value.lower.toordinal() > upper.upper.toordinal() - high_offset
        ):
            return _known(False)
        return _unknown(
            ReasonCode.DATE_PRECISION_INSUFFICIENT,
            "Date precision crosses a permitted interval boundary.",
        )
    return _unsupported()


def compare_values(
    actual: FactValue, expected: ExpectedValue, operator: Operator
) -> PredicateResult:
    if isinstance(actual, UnknownValue):
        return _unknown(ReasonCode.MISSING_PROFILE_FACT, "The applicant fact remains unknown.")
    if isinstance(expected, UnknownValue):
        return _unknown(ReasonCode.AMBIGUOUS_POLICY, "The required value remains unknown.")
    if isinstance(expected, IntervalValue):
        return _interval(actual, expected) if operator == Operator.OVERLAPS else _unsupported()
    if isinstance(actual, GpaValue) and isinstance(expected, GpaValue):
        return compare_gpa(actual, expected, operator)
    if isinstance(actual, DateValue) and isinstance(expected, DateValue):
        return compare_dates(actual, expected, operator)
    if isinstance(actual, StringValue) and isinstance(expected, StringSetValue):
        result = _known(actual.value in expected.values)
    elif isinstance(actual, (CountrySetValue, StringSetValue)) and type(actual) is type(expected):
        assert isinstance(expected, (CountrySetValue, StringSetValue))
        if operator in {Operator.EQ, Operator.NE}:
            result = _known(set(actual.values) == set(expected.values))
            return _invert(result) if operator == Operator.NE else result
        result = _known(bool(set(actual.values) & set(expected.values)))
    elif isinstance(actual, (StringValue, BooleanValue)) and type(actual) is type(expected):
        assert isinstance(expected, (StringValue, BooleanValue))
        if operator not in {Operator.EQ, Operator.NE}:
            return _unsupported()
        result = _known(actual.value == expected.value)
        return _invert(result) if operator == Operator.NE else result
    else:
        return _unsupported()
    if operator not in {Operator.IN, Operator.NOT_IN}:
        return _unsupported()
    return _invert(result) if operator == Operator.NOT_IN else result


@dataclass(frozen=True)
class ExperienceDuration:
    days: Decimal | None
    reason_codes: tuple[ReasonCode, ...] = ()
    intervals: tuple[tuple[date, date], ...] = ()


def experience_duration(
    value: ExperienceValue,
    reference_date: date,
    *,
    require_relevance: bool = True,
    full_time_equivalence: bool = False,
) -> ExperienceDuration:
    if type(reference_date) is not date:
        raise ValueError("Experience requires an explicit calendar reference date")
    if full_time_equivalence or (
        require_relevance and any(entry.relevant is None for entry in value.entries)
    ):
        return ExperienceDuration(None, (ReasonCode.UNSUPPORTED_RULE,))
    intervals = sorted(
        (entry.start, min(entry.end or reference_date, reference_date))
        for entry in value.entries
        if (not require_relevance or entry.relevant) and entry.start < reference_date
    )
    merged: list[tuple[date, date]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return ExperienceDuration(
        Decimal(sum((end - start).days for start, end in merged)), intervals=tuple(merged)
    )


def compare_experience(
    value: ExperienceValue,
    threshold: Decimal,
    operator: Operator,
    reference_date: date,
    *,
    unit: Literal["DAYS", "MONTHS", "YEARS"] = "DAYS",
    full_time_equivalence: bool = False,
) -> PredicateResult:
    if unit != "DAYS":
        return _unsupported()
    duration = experience_duration(
        value, reference_date, full_time_equivalence=full_time_equivalence
    )
    if duration.days is None:
        return _unsupported()
    return compare_decimal(duration.days, threshold, operator)


@dataclass(frozen=True)
class ReferenceDates:
    application: DateValue | None = None
    program_start: DateValue | None = None

    def resolve(self, node: PredicateNode) -> DateValue | None:
        if node.reference_time == ReferenceTime.EXPLICIT:
            return node.reference_date
        return (
            self.application
            if node.reference_time == ReferenceTime.APPLICATION
            else self.program_start
        )


def evaluate_predicate(
    node: PredicateNode, fact: Fact | None, *, references: ReferenceDates | None = None
) -> LeafResult:
    """No source authority/currentness or graph inference is invented by this leaf.

    Upstream publication validates the pinned source bundle. Fact validity uses
    the declared reference event, never execution time. Unsupported aggregate
    experience/language-test rules stay UNKNOWN; callers use explicit pure
    duration helpers rather than an undocumented numeric wire value.
    """
    references = references if references is not None else ReferenceDates()
    matching = fact if fact is not None and fact.attribute.value == node.attribute else None
    if node.attribute not in FactAttribute._value2member_map_:
        result = _unsupported()
    elif node.interpretation == Interpretation.UNRESOLVED:
        result = _unknown(
            ReasonCode.AMBIGUOUS_POLICY, "The source rule interpretation remains unresolved."
        )
    elif matching is None or matching.conflict:
        result = _unknown(
            ReasonCode.MISSING_PROFILE_FACT,
            "A confirmed, nonconflicting matching fact is required.",
        )
    else:
        result = None
        if matching.valid_from is not None or matching.valid_until is not None:
            reference = references.resolve(node)
            if reference is None:
                result = _unknown(
                    ReasonCode.DATE_PRECISION_INSUFFICIENT,
                    "The declared reference event has no known date.",
                )
            else:
                bounds = date_bounds(reference)
                if (matching.valid_from is not None and bounds.lower < matching.valid_from) or (
                    matching.valid_until is not None and bounds.upper > matching.valid_until
                ):
                    result = _unknown(
                        ReasonCode.STALE_EVIDENCE,
                        "Fact validity does not cover every possible reference date.",
                    )
        if result is None:
            if node.operator == Operator.EXISTS:
                if node.evidence_expectation != EvidenceExpectation.REQUIRED_CREDENTIAL:
                    result = _unsupported()
                elif isinstance(node.expected, UnknownValue):
                    result = _unknown(
                        ReasonCode.AMBIGUOUS_POLICY, "The required credential is unspecified."
                    )
                elif isinstance(matching.value, UnknownValue):
                    result = _unknown(
                        ReasonCode.MISSING_PROFILE_FACT, "The required credential is unknown."
                    )
                elif (
                    isinstance(matching.value, BooleanValue)
                    and isinstance(node.expected, BooleanValue)
                    and node.expected.value
                ):
                    result = _known(matching.value.value)
                elif isinstance(matching.value, (CountrySetValue, StringSetValue)):
                    result = compare_values(matching.value, node.expected, Operator.IN)
                elif isinstance(matching.value, StringValue) and isinstance(
                    node.expected, StringValue
                ):
                    result = compare_values(matching.value, node.expected, Operator.EQ)
                else:
                    result = _unsupported()
            else:
                result = compare_values(matching.value, node.expected, node.operator)
    assert result is not None
    return LeafResult(
        node_id=node.id,
        truth=result.truth,
        method=EvaluationMethod.DETERMINISTIC,
        fact_ids=(matching.id,) if matching is not None else (),
        evidence_ids=matching.evidence_ids if matching is not None else (),
        source_span_ids=node.source_span_ids,
        reason_codes=result.reason_codes,
        explanation=result.explanation,
    )
