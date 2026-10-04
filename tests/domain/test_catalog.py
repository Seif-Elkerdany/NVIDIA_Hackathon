import json
import re
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from benefitbridge.domain import dto, enums, facts, requests
from benefitbridge.domain.base import CalendarDate, DecimalText, UtcTimestamp
from benefitbridge.domain.errors import DomainError
from benefitbridge.domain.schema import RESPONSE_MODELS

from .conftest import API_TEXT, SYNTHETIC_STATEMENT, catalog_examples

CATALOG = catalog_examples()
CATALOG_MODELS = {model.__name__: model for model in RESPONSE_MODELS if model.__name__ in CATALOG}


@pytest.mark.parametrize("name", CATALOG)
def test_every_catalog_example_round_trips(name, examples):
    model = CATALOG_MODELS[name]
    payload = examples[name]
    instance = model.model_validate(payload)
    assert json.loads(instance.model_dump_json()) == payload
    assert model.model_validate_json(instance.model_dump_json()) == instance


@pytest.mark.parametrize("name", CATALOG)
def test_catalog_rejects_extra_fields(name, examples):
    with pytest.raises(ValidationError):
        CATALOG_MODELS[name].model_validate({**examples[name], "owner_id": str(UUID(int=1))})


@pytest.mark.parametrize("name", CATALOG)
def test_catalog_required_fields_are_not_silently_defaulted(name, examples):
    model = CATALOG_MODELS[name]
    for field in examples[name]:
        if model.model_fields[field].is_required():
            payload = {key: value for key, value in examples[name].items() if key != field}
            with pytest.raises(ValidationError):
                model.model_validate(payload)


@pytest.mark.parametrize(
    "value",
    [
        "2026-10-20T12:00:00",
        "2026-10-20",
        "2026-10-20T12:00:00+03:00",
        "2026-10-20T12:00:00+00:00",
        "2026-10-20 12:00:00Z",
        "2026-10-20T12:00:00.1234567Z",
        1792497600,
        True,
        datetime(2026, 10, 20),
        datetime(2026, 10, 20, tzinfo=timezone(timedelta(hours=3))),
    ],
)
def test_ambiguous_or_non_wire_timestamps_are_rejected(value):
    with pytest.raises(ValidationError):
        TypeAdapter(UtcTimestamp).validate_python(value)


def test_timestamp_preserves_utc_microseconds():
    adapter = TypeAdapter(UtcTimestamp)
    instant = adapter.validate_python("2026-10-20T12:00:00.123456Z")
    assert instant == datetime(2026, 10, 20, 12, 0, 0, 123456, tzinfo=UTC)
    assert adapter.dump_json(instant) == b'"2026-10-20T12:00:00.123456Z"'


@pytest.mark.parametrize("value", [3.7, True, "NaN", "Infinity", "3e0", "-1", " 3.7", "03.7"])
def test_decimal_wire_values_are_exact_finite_strings(value):
    with pytest.raises(ValidationError):
        TypeAdapter(DecimalText).validate_python(value)


def test_gpa_retains_original_scale_without_conversion():
    grade = facts.GpaValue.model_validate({"type": "GPA", "number": "3.70", "scale_max": "5.00"})
    assert grade.number == Decimal("3.70")
    assert json.loads(grade.model_dump_json()) == {
        "type": "GPA",
        "number": "3.70",
        "scale_max": "5.00",
    }


@pytest.mark.parametrize("number,scale", [("5.01", "5"), ("0", "0"), ("-1", "4"), (3.7, "4")])
def test_invalid_gpa_bounds(number, scale):
    with pytest.raises(ValidationError):
        facts.GpaValue.model_validate({"type": "GPA", "number": number, "scale_max": scale})


@pytest.mark.parametrize(
    "value",
    [
        {"type": "STRING", "value": "3.70"},
        {"type": "GPA", "number": "3.7"},
        {"type": "gpa", "number": "3.7", "scale_max": "4"},
        {"type": "GPA", "number": "3.7", "scale_max": "4", "converted": True},
    ],
)
def test_wrong_gpa_tag_or_shape_is_rejected(value):
    with pytest.raises(ValidationError):
        facts.FactInput.model_validate(
            {"attribute": "education.gpa", "value": value, "evidence_ids": []}
        )


@pytest.mark.parametrize("country", ["eg", "ZZ", "UK", "XK", "USA"])
def test_invalid_country_codes_are_rejected(country):
    with pytest.raises(ValidationError):
        facts.CountrySetValue.model_validate({"type": "COUNTRY_SET", "values": [country]})


def test_known_empty_authorization_is_distinct_from_unknown_and_residence():
    payload = {
        "attribute": "work_authorization.countries",
        "value": {"type": "COUNTRY_SET", "values": []},
        "evidence_ids": [],
    }
    assert facts.FactInput.model_validate(payload).value.values == ()
    payload["attribute"] = "location.country"
    with pytest.raises(ValidationError):
        facts.FactInput.model_validate(payload)
    payload["value"] = {"type": "UNKNOWN", "reason": "NOT_PROVIDED"}
    assert isinstance(facts.FactInput.model_validate(payload).value, facts.UnknownValue)


@pytest.mark.parametrize(
    "value,precision",
    [
        ("2026-02-30", "DAY"),
        ("2026-13", "MONTH"),
        ("2026-01", "YEAR"),
        ("2026", "DAY"),
        ("0000", "YEAR"),
    ],
)
def test_invalid_precision_dates(value, precision):
    with pytest.raises(ValidationError):
        facts.DateValue.model_validate(
            {"type": "DATE", "value": value, "precision": precision, "expected": False}
        )


@pytest.mark.parametrize(
    "value,precision", [("2024-02-29", "DAY"), ("2026-02", "MONTH"), ("2026", "YEAR")]
)
def test_partial_dates_retain_precision(value, precision):
    payload = {"type": "DATE", "value": value, "precision": precision, "expected": True}
    assert facts.DateValue.model_validate(payload).model_dump(mode="json") == payload


@pytest.mark.parametrize("value", ["20261020", "2026-10", "2026-10-20T00:00:00Z", 0])
def test_calendar_dates_do_not_coerce_ambiguous_input(value):
    with pytest.raises(ValidationError):
        TypeAdapter(CalendarDate).validate_python(value)


@pytest.mark.parametrize(
    "enum",
    [
        value
        for value in vars(enums).values()
        if isinstance(value, type) and value.__module__ == enums.__name__
    ],
)
def test_unknown_enum_values_fail(enum):
    with pytest.raises(ValidationError):
        TypeAdapter(enum).validate_python("INVENTED_STATUS")


def test_nested_values_are_immutable_and_json_serializable(examples):
    profile = dto.Profile.model_validate(examples["Profile"])
    with pytest.raises(ValidationError):
        profile.facts[0].value.number = Decimal("4.00")
    assert isinstance(profile.facts, tuple)
    test = facts.LanguageTestEntry.model_validate(
        {
            "test": "Synthetic",
            "total": "7",
            "components": {"writing": "6.5"},
            "taken_on": "2026-01-01",
        }
    )
    with pytest.raises(TypeError):
        test.components["writing"] = Decimal("9")
    assert json.loads(test.model_dump_json())["components"] == {"writing": "6.5"}


def test_unknown_progress_and_decisions_are_not_zero_or_false(examples):
    progress = dto.RunProgress(completed_units=0, total_units=None)
    assert progress.total_units is None
    evaluation = dto.Evaluation.model_validate(examples["Evaluation"])
    assert evaluation.eligibility == enums.Eligibility.UNKNOWN
    assert evaluation.availability == enums.Availability.OPEN
    assert evaluation.fit.score == 75
    assert evaluation.readiness.percent == 67


@pytest.mark.parametrize("percent,required,unknown", [(0, 0, 0), (100, 1, 1), (66, 3, 0)])
def test_readiness_rejects_fabricated_or_inconsistent_percent(percent, required, unknown):
    with pytest.raises(ValidationError):
        dto.Readiness(
            completed=min(2, required),
            required=required,
            percent=percent,
            unknown_applicability=unknown,
        )


def test_fit_rejects_inconsistent_coverage(examples):
    payload = examples["Evaluation"]["fit"]
    payload["coverage"] = 1
    with pytest.raises(ValidationError):
        dto.Fit.model_validate(payload)


def test_safe_error_keeps_typed_field_details():
    error = DomainError(
        "NOT_FOUND",
        "Resource unavailable.",
        404,
        field_errors=(dto.FieldError(path="id", message="Unavailable."),),
    )
    with pytest.raises(DomainError) as caught:
        raise error
    assert str(caught.value) == "Resource unavailable."


REQUESTS = {
    "patch_me": requests.PatchMe,
    "patch_profile": requests.PatchProfile,
    "create_document_upload": requests.CreateDocumentUpload,
    "complete_document_upload": requests.CompleteDocumentUpload,
    "review_fact_candidates": requests.ReviewFactCandidates,
    "start_discovery": requests.StartDiscovery,
    "import_opportunity": requests.ImportOpportunity,
    "cancel_run": requests.EmptyCommand,
    "answer_clarifications": requests.AnswerClarifications,
    "start_evaluation": requests.StartEvaluation,
    "refresh_opportunity": requests.EmptyCommand,
    "save_opportunity": requests.EmptyCommand,
    "create_application": requests.CreateApplication,
    "patch_checklist_item": requests.PatchChecklistItem,
    "start_draft": requests.StartDraft,
    "edit_draft": requests.EditDraft,
    "accept_draft": requests.AcceptDraft,
    "delete_account": requests.DeleteAccount,
    "reset_demo": requests.ResetDemo,
    "create_watch": requests.CreateWatch,
    "patch_watch": requests.PatchWatch,
    "read_notification": requests.EmptyCommand,
}


@pytest.mark.parametrize("operation,model", REQUESTS.items())
def test_documented_request_payloads(operation, model):
    section = API_TEXT.split(f"### `{operation}`")[1].split("**Request**")[1].split("**Response")[0]
    payload = json.loads(re.search(r"```json\n(.*?)\n```", section, re.S).group(1))
    if operation == "edit_draft":
        payload["text"] = SYNTHETIC_STATEMENT
    instance = model.model_validate(payload)
    assert json.loads(instance.model_dump_json()) == payload
    with pytest.raises(ValidationError):
        model.model_validate({**payload, "owner_id": str(UUID(int=1))})


@pytest.mark.parametrize("confirmation", [1, "true", False, None])
def test_draft_acceptance_requires_literal_json_true(confirmation):
    with pytest.raises(ValidationError):
        requests.AcceptDraft(base_application_revision=1, confirmed_review=confirmation)


def test_patch_rules_and_review_decisions():
    with pytest.raises(ValidationError):
        requests.PatchMe()
    with pytest.raises(ValidationError):
        requests.PatchMe(display_name=None)
    with pytest.raises(ValidationError):
        requests.PatchWatch(base_revision=1)
    with pytest.raises(ValidationError):
        requests.CorrectCandidate(
            candidate_id=UUID(int=1), action="CORRECT", value={"type": "BOOLEAN", "value": True}
        )
    with pytest.raises(ValidationError):
        requests.AcceptCandidate(candidate_id=UUID(int=1), action="ACCEPT", explanation="Forbidden")


def test_deadline_does_not_invent_midnight(examples):
    deadline = dto.Deadline.model_validate(examples["Deadline"])
    assert deadline.date == "2026-11-30" and deadline.at is None
    with pytest.raises(ValidationError):
        dto.Deadline.model_validate({**examples["Deadline"], "at": "2026-11-30T00:00:00Z"})


@pytest.mark.parametrize("interval", [24.0, "24", True, 48])
def test_watch_intervals_require_documented_json_integers(interval):
    with pytest.raises(ValidationError):
        requests.CreateWatch(opportunity_id=UUID(int=1), interval_hours=interval)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org",
        "https://example.org:bad",
        "https://example.org:70000",
        "https://user:secret@example.org",
        "https://example.org/a b",
    ],
)
def test_import_urls_validate_syntax_without_network(url):
    with pytest.raises(ValidationError):
        requests.ImportOpportunity(profile_version_id=UUID(int=1), url=url)


@pytest.mark.parametrize("name", ["Africa/Cairo", "UTC", "America/New_York"])
def test_pinned_timezone_names_work_without_system_tzdata(examples, name):
    account = dto.Account.model_validate({**examples["Account"], "timezone": name})
    assert account.timezone == name
    with pytest.raises(ValidationError):
        dto.Account.model_validate({**examples["Account"], "timezone": "Invented/Timezone"})


def test_unicode_spans_use_code_points_not_utf8_bytes(examples):
    span = {**examples["Evidence"], "quote": "A🙂é", "start": 4, "end": 7}
    dto.Evidence.model_validate(span)
    with pytest.raises(ValidationError):
        dto.Evidence.model_validate({**span, "end": 4 + len(span["quote"].encode("utf-8"))})
