"""Shared wire primitives. Validation never consults an ambient clock or network."""

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from importlib.resources import files
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    StrictInt,
    StrictStr,
    WithJsonSchema,
)

_reference = json.loads(files(__package__).joinpath("reference_data.json").read_text("utf-8"))
COUNTRY_CODES: frozenset[str] = frozenset(_reference["country_codes"])
TIMEZONE_NAMES: frozenset[str] = frozenset(_reference["timezones"])
DECIMAL_PATTERN = r"^(0|[1-9][0-9]*)(\.[0-9]+)?$"
TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$"


class DomainModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )


def unique_items[T](values: tuple[T, ...]) -> tuple[T, ...]:
    if len(set(values)) != len(values):
        raise ValueError("Duplicate values are not allowed")
    return values


def decimal_value(value: object) -> Decimal:
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, str) and re.fullmatch(DECIMAL_PATTERN, value):
        result = Decimal(value)
    else:
        raise ValueError("Exact quantities require a nonnegative decimal string")
    if not result.is_finite() or result < 0:
        raise ValueError("Exact quantities must be finite and nonnegative")
    return result


def utc_timestamp(value: object) -> datetime:
    if isinstance(value, str) and re.fullmatch(TIMESTAMP_PATTERN, value):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be UTC and use RFC3339 with Z")
    return value


def calendar_date(value: object) -> date:
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return date.fromisoformat(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raise ValueError("Date must use YYYY-MM-DD without a time")


def validate_partial_date(value: str, precision: str) -> None:
    patterns = {
        "DAY": r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
        "MONTH": r"[0-9]{4}-[0-9]{2}",
        "YEAR": r"[0-9]{4}",
    }
    if not re.fullmatch(patterns[precision], value):
        raise ValueError("Date representation must match its precision")
    date.fromisoformat(value + {"DAY": "", "MONTH": "-01", "YEAR": "-01-01"}[precision])


def country_code(value: str) -> str:
    if value not in COUNTRY_CODES:
        raise ValueError("Country must be an assigned uppercase ISO-3166 alpha-2 code")
    return value


def timezone_name(value: str) -> str:
    if value not in TIMEZONE_NAMES:
        raise ValueError("Timezone must be an IANA timezone name")
    return value


def https_url(value: str) -> str:
    parsed = urlsplit(value)
    # Accessing port validates malformed and out-of-range port syntax without I/O.
    port = parsed.port
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port == 0
        or any(c.isspace() or ord(c) < 32 for c in value)
    ):
        raise ValueError("URL must be absolute HTTPS without credentials or whitespace")
    # Network and redirect authorization belongs to the guarded fetch/storage adapter.
    return value


def statement_text(value: str) -> str:
    if not 150 <= len(value.split()) <= 500:
        raise ValueError("Statement must contain 150 to 500 whitespace-separated words")
    return value


def watch_interval(value: object) -> Literal[24, 72]:
    if type(value) is int and value == 24:
        return 24
    if type(value) is int and value == 72:
        return 72
    raise ValueError("Watch interval must be the JSON integer 24 or 72")


NonEmpty = Annotated[StrictStr, Field(min_length=1)]
ShortText = Annotated[StrictStr, Field(min_length=1, max_length=80)]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]
PositiveInt = Annotated[StrictInt, Field(ge=1)]
Sha256 = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
CountryCode = Annotated[
    StrictStr,
    AfterValidator(country_code),
    Field(json_schema_extra={"enum": sorted(COUNTRY_CODES)}),
]
TimezoneName = Annotated[StrictStr, AfterValidator(timezone_name), Field(min_length=1)]
HttpsUrl = Annotated[StrictStr, Field(min_length=1), AfterValidator(https_url)]
WatchInterval = Annotated[Literal[24, 72], BeforeValidator(watch_interval)]
StatementText = Annotated[StrictStr, Field(max_length=8000), AfterValidator(statement_text)]
UUIDs = Annotated[
    tuple[UUID, ...], AfterValidator(unique_items), Field(json_schema_extra={"uniqueItems": True})
]
DecimalText = Annotated[
    Decimal,
    BeforeValidator(decimal_value),
    PlainSerializer(lambda v: format(v, "f"), return_type=str),
    WithJsonSchema({"type": "string", "pattern": DECIMAL_PATTERN}),
]
UtcTimestamp = Annotated[
    datetime,
    BeforeValidator(utc_timestamp),
    PlainSerializer(lambda v: v.isoformat().replace("+00:00", "Z"), return_type=str),
    WithJsonSchema({"type": "string", "format": "date-time", "pattern": TIMESTAMP_PATTERN}),
]
CalendarDate = Annotated[date, BeforeValidator(calendar_date)]
