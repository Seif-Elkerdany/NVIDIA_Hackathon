from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from itertools import permutations
from uuid import UUID

import pytest
from pydantic import ValidationError
from tests.fakes.providers import FakeClock

from benefitbridge.domain.dto import Deadline
from benefitbridge.domain.enums import (
    DatePrecision,
    EvidenceExpectation,
    FactAttribute,
    Operator,
    ReasonCode,
    ReferenceTime,
    Truth,
)
from benefitbridge.domain.facts import (
    BooleanValue,
    CountrySetValue,
    DateValue,
    ExperienceEntry,
    ExperienceValue,
    Fact,
    GpaValue,
    StringSetValue,
    StringValue,
    UnknownValue,
)
from benefitbridge.domain.rules import IntervalValue, PredicateNode
from benefitbridge.eligibility.predicates import (
    ReferenceDates,
    compare_dates,
    compare_deadline,
    compare_decimal,
    compare_experience,
    compare_gpa,
    compare_values,
    date_bounds,
    evaluate_predicate,
    experience_duration,
)


def gpa(number: str = "3.70", scale: str = "4.00") -> GpaValue:
    return GpaValue(type="GPA", number=number, scale_max=scale)


def day(value: str, precision: DatePrecision = DatePrecision.DAY) -> DateValue:
    return DateValue(type="DATE", value=value, precision=precision, expected=False)


def node(**changes: object) -> PredicateNode:
    return PredicateNode.model_validate(
        {
            "id": "synthetic-rule",
            "type": "PREDICATE",
            "modality": "MANDATORY",
            "attribute": "education.gpa",
            "operator": "GTE",
            "expected": gpa("3.0"),
            "source_span_ids": [UUID(int=1)],
            "scope": {"cycle": "synthetic-cycle", "location_countries": []},
            "reference_time": "APPLICATION",
            "interpretation": "DIRECT",
            "evidence_expectation": "KNOWN_FACT",
        }
        | changes
    )


def fact(**changes: object) -> Fact:
    return Fact.model_validate(
        {
            "id": UUID(int=2),
            "attribute": "education.gpa",
            "value": gpa(),
            "evidence_ids": [],
            "provenance": "USER_CONFIRMED",
            "confirmed_at": FakeClock().now(),
            "valid_from": None,
            "valid_until": None,
            "conflict": False,
        }
        | changes
    )


@pytest.mark.parametrize(
    "operator,truth",
    [
        (Operator.EQ, Truth.TRUE),
        (Operator.NE, Truth.FALSE),
        (Operator.GT, Truth.FALSE),
        (Operator.GTE, Truth.TRUE),
        (Operator.LT, Truth.FALSE),
        (Operator.LTE, Truth.TRUE),
    ],
)
def test_decimal_equality_boundaries_without_rounding(operator: Operator, truth: Truth) -> None:
    with localcontext() as context:
        context.prec = 2
        assert (
            compare_decimal(
                Decimal("3.700000000000000000000001"),
                Decimal("3.700000000000000000000001"),
                operator,
            ).truth
            == truth
        )
        assert (
            compare_decimal(
                Decimal("3.700000000000000000000001"), Decimal("3.7"), Operator.GT
            ).truth
            == Truth.TRUE
        )


@pytest.mark.parametrize(
    "operator", [Operator.EQ, Operator.NE, Operator.GT, Operator.GTE, Operator.LT, Operator.LTE]
)
def test_gpa_does_not_normalize_incompatible_scales(operator: Operator) -> None:
    result = compare_gpa(gpa("3.5", "5"), gpa("3.0", "4"), operator)
    assert result.truth == Truth.UNKNOWN and result.reason_codes == (ReasonCode.INCOMPATIBLE_SCALE,)


def test_known_gpa_missing_scale_and_nondecimal_values() -> None:
    assert compare_gpa(gpa(), gpa("3.0"), Operator.GTE).truth == Truth.TRUE
    assert compare_gpa(gpa("3.000"), gpa("3.0", "4.0"), Operator.EQ).truth == Truth.TRUE
    assert compare_gpa(gpa(), None, Operator.GTE).truth == Truth.UNKNOWN
    with pytest.raises(ValidationError):
        GpaValue.model_validate({"type": "GPA", "number": "3.7"})
    assert compare_decimal(Decimal("NaN"), Decimal("3"), Operator.EQ).truth == Truth.UNKNOWN
    assert compare_decimal(None, Decimal("3"), Operator.GTE).truth == Truth.UNKNOWN


@pytest.mark.parametrize(
    "known,expected,operator,truth",
    [
        (("EG",), ("EG", "US"), Operator.IN, Truth.TRUE),
        (("EG",), ("US",), Operator.IN, Truth.FALSE),
        ((), ("EG",), Operator.IN, Truth.FALSE),
        ((), ("EG",), Operator.NOT_IN, Truth.TRUE),
        (("EG", "US"), ("EG",), Operator.NOT_IN, Truth.FALSE),
        (("EG", "US"), ("US", "EG"), Operator.EQ, Truth.TRUE),
        (("EG",), ("EG", "US"), Operator.EQ, Truth.FALSE),
    ],
)
def test_country_set_existential_membership_and_known_empty_sets(
    known: tuple[str, ...], expected: tuple[str, ...], operator: Operator, truth: Truth
) -> None:
    result = compare_values(
        CountrySetValue(type="COUNTRY_SET", values=known),
        CountrySetValue(type="COUNTRY_SET", values=expected),
        operator,
    )
    assert result.truth == truth


def test_category_membership_is_exact_and_unknown_is_not_known_empty() -> None:
    actual = StringValue(type="STRING", value="UNDERGRADUATE")
    allowed = StringSetValue(type="STRING_SET", values=("UNDERGRADUATE", "GRADUATE"))
    assert compare_values(actual, allowed, Operator.IN).truth == Truth.TRUE
    assert (
        compare_values(
            StringValue(type="STRING", value="undergraduate"), allowed, Operator.IN
        ).truth
        == Truth.FALSE
    )
    unknown = UnknownValue(type="UNKNOWN", reason="NOT_PROVIDED")
    assert compare_values(unknown, allowed, Operator.NOT_IN).truth == Truth.UNKNOWN
    assert compare_values(actual, unknown, Operator.EQ).truth == Truth.UNKNOWN
    assert compare_values(actual, actual, Operator.GT).truth == Truth.UNKNOWN
    assert compare_values(actual, actual, Operator.SEMANTIC_MATCH).truth == Truth.UNKNOWN


@pytest.mark.parametrize(
    "actual,expected,operator,truth",
    [
        ("2026-05", "2026-06-01", Operator.BEFORE, Truth.TRUE),
        ("2026-05", "2026-05-15", Operator.BEFORE, Truth.UNKNOWN),
        ("2026-05", "2026-05-01", Operator.LT, Truth.FALSE),
        ("2026-05", "2026-05-31", Operator.LTE, Truth.TRUE),
        ("2026-05", "2026-05-01", Operator.GTE, Truth.TRUE),
        ("2026-05", "2026-05-01", Operator.GT, Truth.UNKNOWN),
        ("2026-05-15", "2026-05-15", Operator.BEFORE, Truth.FALSE),
        ("2026-05-15", "2026-05-15", Operator.AFTER, Truth.FALSE),
        ("2026-05-15", "2026-05-15", Operator.EQ, Truth.TRUE),
        ("2026-05", "2026-05", Operator.EQ, Truth.UNKNOWN),
        ("2026", "2027", Operator.NE, Truth.TRUE),
        ("2026", "2026-05", Operator.NE, Truth.UNKNOWN),
    ],
)
def test_precision_aware_date_boundaries(
    actual: str, expected: str, operator: Operator, truth: Truth
) -> None:
    def value(raw: str) -> DateValue:
        return day(
            raw, {4: DatePrecision.YEAR, 7: DatePrecision.MONTH, 10: DatePrecision.DAY}[len(raw)]
        )

    assert compare_dates(value(actual), value(expected), operator).truth == truth


def test_leap_year_and_maximum_year_bounds_do_not_overflow() -> None:
    assert date_bounds(day("2024-02", DatePrecision.MONTH)).upper == date(2024, 2, 29)
    assert date_bounds(day("2023-02", DatePrecision.MONTH)).upper == date(2023, 2, 28)
    assert date_bounds(day("9999", DatePrecision.YEAR)).upper == date.max


def test_partial_dates_agree_with_exhaustive_calendar_possibilities() -> None:
    actual = day("2024-02", DatePrecision.MONTH)
    for expected in ("2024-02-01", "2024-02-15", "2024-02-29", "2024-03-01"):
        for operator in (
            Operator.EQ,
            Operator.NE,
            Operator.LT,
            Operator.LTE,
            Operator.GT,
            Operator.GTE,
        ):
            outcomes = {
                compare_dates(day(f"2024-02-{number:02d}"), day(expected), operator).truth
                for number in range(1, 30)
            }
            result = next(iter(outcomes)) if len(outcomes) == 1 else Truth.UNKNOWN
            assert compare_dates(actual, day(expected), operator).truth == result


def test_date_and_gpa_intervals_preserve_inclusive_bounds_and_uncertainty() -> None:
    interval = IntervalValue(
        type="INTERVAL",
        lower=day("2026-01-01"),
        upper=day("2026-12-31"),
        lower_inclusive=True,
        upper_inclusive=False,
    )
    assert (
        compare_values(day("2026-05", DatePrecision.MONTH), interval, Operator.OVERLAPS).truth
        == Truth.TRUE
    )
    assert (
        compare_values(day("2026", DatePrecision.YEAR), interval, Operator.OVERLAPS).truth
        == Truth.UNKNOWN
    )
    assert compare_values(day("2026-12-31"), interval, Operator.OVERLAPS).truth == Truth.FALSE
    assert (
        compare_values(day("2027", DatePrecision.YEAR), interval, Operator.OVERLAPS).truth
        == Truth.FALSE
    )
    numbers = IntervalValue(
        type="INTERVAL",
        lower=gpa("3.0"),
        upper=gpa("3.5"),
        lower_inclusive=False,
        upper_inclusive=True,
    )
    assert compare_values(gpa("3.0"), numbers, Operator.OVERLAPS).truth == Truth.FALSE
    assert compare_values(gpa("3.5"), numbers, Operator.OVERLAPS).truth == Truth.TRUE
    assert compare_values(gpa("3.5", "5"), numbers, Operator.OVERLAPS).truth == Truth.UNKNOWN


def test_date_only_deadlines_do_not_invent_midnight_and_keep_timezone() -> None:
    cutoff = Deadline(
        raw_text="Synthetic date",
        precision="DATE",
        date="2026-01-01",
        at=None,
        timezone="America/New_York",
        ambiguity=None,
    )
    assert (
        compare_deadline(datetime(2026, 1, 1, 1, tzinfo=UTC), cutoff, Operator.BEFORE).truth
        == Truth.TRUE
    )
    assert (
        compare_deadline(datetime(2026, 1, 1, 12, tzinfo=UTC), cutoff, Operator.BEFORE).truth
        == Truth.UNKNOWN
    )
    assert (
        compare_deadline(datetime(2026, 1, 2, 6, tzinfo=UTC), cutoff, Operator.AFTER).truth
        == Truth.TRUE
    )
    assert compare_deadline(datetime(2026, 1, 1), cutoff, Operator.BEFORE).truth == Truth.UNKNOWN
    assert (
        compare_deadline(
            FakeClock().now(), cutoff.model_copy(update={"timezone": None}), Operator.AFTER
        ).truth
        == Truth.UNKNOWN
    )


def test_instant_deadline_compares_equal_instants_across_offsets_and_unknown_precision() -> None:
    instant = Deadline(
        raw_text="Synthetic instant",
        precision="INSTANT",
        date=None,
        at="2026-10-04T12:00:00Z",
        timezone=None,
        ambiguity=None,
    )
    same = datetime(2026, 10, 4, 15, tzinfo=timezone(timedelta(hours=3)))
    assert compare_deadline(same, instant, Operator.EQ).truth == Truth.TRUE
    assert compare_deadline(same, instant, Operator.GT).truth == Truth.FALSE
    unknown = Deadline(
        raw_text="Not specified",
        precision="UNKNOWN",
        date=None,
        at=None,
        timezone=None,
        ambiguity=None,
    )
    assert compare_deadline(same, unknown, Operator.BEFORE).truth == Truth.UNKNOWN
    assert compare_deadline(
        same, instant.model_copy(update={"ambiguity": "Unresolved"}), Operator.LTE
    ).reason_codes == (ReasonCode.AMBIGUOUS_POLICY,)


def job(start: str, end: str | None, relevant: bool | None = True) -> ExperienceEntry:
    return ExperienceEntry(role="Synthetic role", start=start, end=end, relevant=relevant)


def test_experience_unions_overlapping_nested_touching_and_duplicate_jobs() -> None:
    entries = (
        job("2026-01-01", "2026-01-11"),
        job("2026-01-06", "2026-01-16"),
        job("2026-01-03", "2026-01-05"),
        job("2026-01-16", "2026-01-21"),
    )
    for ordered in permutations(entries):
        result = experience_duration(
            ExperienceValue(type="EXPERIENCE", entries=ordered), date(2026, 2, 1)
        )
        assert result.days == Decimal(20)
        assert result.intervals == ((date(2026, 1, 1), date(2026, 1, 21)),)
    duplicate = ExperienceValue(type="EXPERIENCE", entries=(entries[0], entries[0]))
    assert experience_duration(duplicate, date(2026, 2, 1)).days == Decimal(10)


def test_experience_clips_ongoing_future_and_irrelevant_intervals_to_reference_date() -> None:
    value = ExperienceValue(
        type="EXPERIENCE",
        entries=(
            job("2026-01-01", None),
            job("2026-01-05", "2026-03-01"),
            job("2027-01-01", None),
            job("2025-01-01", "2025-02-01", False),
        ),
    )
    reference = date(2026, 1, 11)
    assert experience_duration(value, reference).days == Decimal(10)
    assert compare_experience(value, Decimal(10), Operator.GTE, reference).truth == Truth.TRUE
    assert compare_experience(value, Decimal(10), Operator.GT, reference).truth == Truth.FALSE
    assert (
        compare_experience(value, Decimal(1), Operator.GTE, reference, unit="MONTHS").truth
        == Truth.UNKNOWN
    )
    assert experience_duration(value, reference, full_time_equivalence=True).days is None
    assert experience_duration(
        ExperienceValue(type="EXPERIENCE", entries=()), reference
    ).days == Decimal(0)
    uncertain = ExperienceValue(type="EXPERIENCE", entries=(job("2026-01-01", None, None),))
    assert experience_duration(uncertain, reference).days is None


def test_leaf_results_reuse_shared_dtos_and_source_fact_provenance() -> None:
    rule, known = node(), fact(evidence_ids=(UUID(int=3),), provenance="USER_CONFIRMED_DOCUMENT")
    result = evaluate_predicate(rule, known)
    assert result.truth == Truth.TRUE
    assert result.fact_ids == (known.id,) and result.evidence_ids == known.evidence_ids
    assert result.source_span_ids == rule.source_span_ids and result.method == "DETERMINISTIC"
    assert not result.reason_codes


def test_missing_conflicting_mismatched_and_unsupported_facts_are_unknown() -> None:
    for value in (
        None,
        fact(value=UnknownValue(type="UNKNOWN", reason="NOT_PROVIDED")),
        fact(conflict=True, provenance="CONFLICTING"),
    ):
        assert evaluate_predicate(node(), value).truth == Truth.UNKNOWN
    unmatched = fact(
        attribute=FactAttribute.EDUCATION_ENROLLED, value=BooleanValue(type="BOOLEAN", value=True)
    )
    assert evaluate_predicate(node(), unmatched).fact_ids == ()
    assert evaluate_predicate(node(attribute="unsupported_attribute"), fact()).reason_codes == (
        ReasonCode.UNSUPPORTED_RULE,
    )
    assert evaluate_predicate(node(interpretation="UNRESOLVED"), fact()).reason_codes == (
        ReasonCode.AMBIGUOUS_POLICY,
    )


def test_fact_validity_uses_declared_event_not_ambient_time_and_partial_dates_fail_closed() -> None:
    known = fact(valid_from="2026-01-01", valid_until="2026-05-31")
    references = ReferenceDates(application=day("2026-05-31"), program_start=day("2026-06-01"))
    assert evaluate_predicate(node(), known, references=references).truth == Truth.TRUE
    assert evaluate_predicate(
        node(reference_time=ReferenceTime.PROGRAM_START), known, references=references
    ).reason_codes == (ReasonCode.STALE_EVIDENCE,)
    assert evaluate_predicate(node(), known).reason_codes == (
        ReasonCode.DATE_PRECISION_INSUFFICIENT,
    )
    partial = ReferenceDates(application=day("2026", DatePrecision.YEAR))
    assert evaluate_predicate(node(), known, references=partial).truth == Truth.UNKNOWN
    explicit = node(reference_time=ReferenceTime.EXPLICIT, reference_date=day("2026-05-31"))
    assert evaluate_predicate(explicit, known).truth == Truth.TRUE


def test_exists_requires_known_possession_of_the_explicit_credential() -> None:
    known = fact(attribute="skills", value=StringSetValue(type="STRING_SET", values=("Python",)))
    required = node(
        attribute="skills",
        operator=Operator.EXISTS,
        expected=StringSetValue(type="STRING_SET", values=("Python",)),
        evidence_expectation=EvidenceExpectation.REQUIRED_CREDENTIAL,
    )
    assert evaluate_predicate(required, known).truth == Truth.TRUE
    other = required.model_copy(
        update={"expected": StringSetValue(type="STRING_SET", values=("Rust",))}
    )
    assert evaluate_predicate(other, known).truth == Truth.FALSE
    assert evaluate_predicate(required, None).truth == Truth.UNKNOWN
    assert (
        evaluate_predicate(
            required.model_copy(update={"evidence_expectation": EvidenceExpectation.KNOWN_FACT}),
            known,
        ).truth
        == Truth.UNKNOWN
    )


def test_deadline_dst_boundary_and_missing_timezone_data_are_conservative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from zoneinfo import ZoneInfoNotFoundError

    from benefitbridge.eligibility import predicates

    deadline = Deadline(
        raw_text="Synthetic DST cutoff",
        precision="DATE",
        date="2026-03-08",
        at=None,
        timezone="America/New_York",
        ambiguity=None,
    )
    assert (
        compare_deadline(datetime(2026, 3, 8, 4, 59, tzinfo=UTC), deadline, Operator.BEFORE).truth
        == Truth.TRUE
    )
    assert (
        compare_deadline(datetime(2026, 3, 8, 7, 30, tzinfo=UTC), deadline, Operator.LTE).truth
        == Truth.UNKNOWN
    )
    assert (
        compare_deadline(datetime(2026, 3, 9, 4, tzinfo=UTC), deadline, Operator.AFTER).truth
        == Truth.TRUE
    )

    def missing_zone(name: str) -> None:
        raise ZoneInfoNotFoundError(name)

    monkeypatch.setattr(predicates, "ZoneInfo", missing_zone)
    assert compare_deadline(FakeClock().now(), deadline, Operator.AFTER).truth == Truth.UNKNOWN


def test_ambiguous_date_interval_does_not_select_convenient_bounds() -> None:
    ambiguous = IntervalValue(
        type="INTERVAL",
        lower=day("2026-05", DatePrecision.MONTH),
        upper=day("2026-05-15"),
        lower_inclusive=True,
        upper_inclusive=True,
    )
    result = compare_values(day("2026-05-10"), ambiguous, Operator.OVERLAPS)
    assert result.truth == Truth.UNKNOWN and result.reason_codes == (ReasonCode.AMBIGUOUS_POLICY,)


def test_experience_leap_days_separate_jobs_and_zero_length_intervals() -> None:
    value = ExperienceValue(
        type="EXPERIENCE",
        entries=(
            job("2024-02-28", "2024-03-01"),
            job("2024-03-05", "2024-03-08"),
            job("2024-03-09", "2024-03-09"),
        ),
    )
    duration = experience_duration(value, date(2024, 3, 20))
    assert duration.days == Decimal(5)
    with pytest.raises(ValueError, match="calendar reference"):
        experience_duration(value, datetime(2024, 3, 20, tzinfo=UTC))
