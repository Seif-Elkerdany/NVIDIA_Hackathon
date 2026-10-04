"""Tagged applicant facts, preserving original scales and explicit unknown values."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, Field, PlainSerializer, StrictBool, StrictStr, model_validator

from .base import (
    CalendarDate,
    CountryCode,
    DecimalText,
    DomainModel,
    NonEmpty,
    ShortText,
    UtcTimestamp,
    UUIDs,
    unique_items,
    validate_partial_date,
)
from .enums import CandidateState, DatePrecision, FactAttribute, FactType, Provenance, UnknownReason


class StringValue(DomainModel):
    type: Literal[FactType.STRING]
    value: Annotated[StrictStr, Field(min_length=1, max_length=500)]


class BooleanValue(DomainModel):
    type: Literal[FactType.BOOLEAN]
    value: StrictBool


class CountrySetValue(DomainModel):
    type: Literal[FactType.COUNTRY_SET]
    values: Annotated[
        tuple[CountryCode, ...],
        Field(max_length=20, json_schema_extra={"uniqueItems": True}),
        AfterValidator(unique_items),
    ]


class StringSetValue(DomainModel):
    type: Literal[FactType.STRING_SET]
    values: Annotated[
        tuple[ShortText, ...],
        Field(max_length=50, json_schema_extra={"uniqueItems": True}),
        AfterValidator(unique_items),
    ]


class GpaValue(DomainModel):
    type: Literal[FactType.GPA]
    number: DecimalText
    scale_max: DecimalText

    @model_validator(mode="after")
    def valid_scale(self) -> Self:
        if self.scale_max <= 0 or self.number > self.scale_max:
            raise ValueError("GPA requires 0 <= number <= scale_max and scale_max > 0")
        return self


class DateValue(DomainModel):
    type: Literal[FactType.DATE]
    value: StrictStr
    precision: DatePrecision
    expected: StrictBool

    @model_validator(mode="after")
    def valid_precision(self) -> Self:
        validate_partial_date(self.value, self.precision)
        return self


class ExperienceEntry(DomainModel):
    role: NonEmpty
    start: CalendarDate
    end: CalendarDate | None
    relevant: StrictBool | None

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        if self.end is not None and self.end < self.start:
            raise ValueError("Experience end cannot precede start")
        return self


class ExperienceValue(DomainModel):
    type: Literal[FactType.EXPERIENCE]
    entries: Annotated[tuple[ExperienceEntry, ...], Field(max_length=20)]


class LanguageTestEntry(DomainModel):
    test: NonEmpty
    total: DecimalText
    components: Annotated[
        Mapping[str, DecimalText],
        AfterValidator(MappingProxyType),
        PlainSerializer(dict, return_type=dict[str, DecimalText]),
    ]
    taken_on: CalendarDate


class LanguageTestsValue(DomainModel):
    type: Literal[FactType.LANGUAGE_TESTS]
    entries: Annotated[tuple[LanguageTestEntry, ...], Field(max_length=10)]


class UnknownValue(DomainModel):
    type: Literal[FactType.UNKNOWN]
    reason: UnknownReason


FactValue = Annotated[
    StringValue
    | BooleanValue
    | CountrySetValue
    | StringSetValue
    | GpaValue
    | DateValue
    | ExperienceValue
    | LanguageTestsValue
    | UnknownValue,
    Field(discriminator="type"),
]

ATTRIBUTE_TYPES: Mapping[FactAttribute, type[DomainModel]] = MappingProxyType(
    {
        FactAttribute.LOCATION_COUNTRY: CountrySetValue,
        FactAttribute.CITIZENSHIP_COUNTRIES: CountrySetValue,
        FactAttribute.WORK_AUTHORIZATION_COUNTRIES: CountrySetValue,
        FactAttribute.EDUCATION_ENROLLED: BooleanValue,
        FactAttribute.EDUCATION_LEVEL: StringValue,
        FactAttribute.EDUCATION_FIELD: StringValue,
        FactAttribute.EDUCATION_INSTITUTION: StringValue,
        FactAttribute.EDUCATION_GRADUATION: DateValue,
        FactAttribute.DATE_OF_BIRTH: DateValue,
        FactAttribute.EDUCATION_GPA: GpaValue,
        FactAttribute.SKILLS: StringSetValue,
        FactAttribute.EXPERIENCE: ExperienceValue,
        FactAttribute.LANGUAGE_TESTS: LanguageTestsValue,
    }
)


def validate_fact_value(attribute: FactAttribute, value: FactValue) -> None:
    if isinstance(value, UnknownValue):
        return
    if not isinstance(value, ATTRIBUTE_TYPES[attribute]):
        raise ValueError("Fact value tag does not match its attribute")
    if (
        attribute == FactAttribute.LOCATION_COUNTRY
        and isinstance(value, CountrySetValue)
        and len(value.values) != 1
    ):
        raise ValueError("Known residence must contain exactly one country")


class FactInput(DomainModel):
    attribute: FactAttribute
    value: FactValue
    evidence_ids: UUIDs

    @model_validator(mode="after")
    def matching_attribute(self) -> Self:
        validate_fact_value(self.attribute, self.value)
        return self


class Fact(FactInput):
    id: UUID
    provenance: Provenance
    confirmed_at: UtcTimestamp
    valid_from: CalendarDate | None
    valid_until: CalendarDate | None
    conflict: StrictBool

    @model_validator(mode="after")
    def valid_provenance(self) -> Self:
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise ValueError("Fact validity end cannot precede start")
        if self.provenance == Provenance.USER_CONFIRMED_DOCUMENT and not self.evidence_ids:
            raise ValueError("Document-confirmed facts require evidence references")
        if (self.provenance == Provenance.CONFLICTING) != self.conflict:
            raise ValueError("Conflicting provenance and conflict flag must agree")
        return self


class FactCandidate(FactInput):
    id: UUID
    document_id: UUID
    state: CandidateState
    issues: tuple[NonEmpty, ...]
