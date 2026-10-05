"""Authenticated immutable profiles, race/conflict and private evidence boundaries."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import func, select, update
from tests.api import test_accounts as accounts
from tests.integration import test_documents as docs
from tests.integration import test_identity as identity

from benefitbridge.config import Settings
from benefitbridge.db.documents import DocumentRecord
from benefitbridge.db.jobs import IdempotencyRecord, OutboxRecord, RunRecord

database = identity.database
account_client = accounts.account_client
evidence = docs.evidence


def test_profile_production_requires_private_invalidation_handler():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from tests.ports.fakes import FakeStage

    from benefitbridge.api import profiles
    from benefitbridge.composition import Dependencies, HandlerBinding
    from benefitbridge.config import ConfigurationError
    from benefitbridge.domain.enums import RunKind
    from benefitbridge.ports import JobScope

    bindings = {kind.value: HandlerBinding(FakeStage()) for kind in RunKind}
    app = FastAPI()
    app.state.settings = Settings(_env_file=None).model_copy(update={"app_env": "production"})
    app.state.dependencies = Dependencies(handlers=bindings)
    app.include_router(profiles.router)
    for binding in (None, HandlerBinding(FakeStage(), JobScope.PUBLIC)):
        if binding is not None:
            bindings["PROFILE_INVALIDATE"] = binding
        app.state.dependencies = Dependencies(handlers=bindings)
        with pytest.raises(ConfigurationError, match="PROFILE_INVALIDATE"), TestClient(app):
            pass
    bindings["PROFILE_INVALIDATE"] = HandlerBinding(FakeStage())
    app.state.dependencies = Dependencies(handlers=bindings)
    with TestClient(app):
        pass


@pytest.fixture
def client(account_client):
    http, _, admin, clock = account_client
    http.app.state.settings = Settings(
        _env_file=None, app_env="test", receipt_encryption_key="synthetic-profile-replay-key-00000"
    )
    return http, admin, clock


def headers(clock, owner=accounts.SUBJECT, key=None):
    result = {"Authorization": "Bearer " + accounts.token(clock, {"sub": str(owner)})}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def consent(client, owner=accounts.SUBJECT):
    http, _, clock = client
    assert (
        http.patch(
            "/api/v1/me", headers=headers(clock, owner), json={"consent_version": "2026-10-01"}
        ).status_code
        == 200
    )


def patch(base, attribute="education.gpa", value=None, evidence_ids=()):
    return {
        "base_profile_version_id": str(base),
        "changes": [
            {
                "attribute": attribute,
                "value": value or {"type": "GPA", "number": "3.70", "scale_max": "4.00"},
                "evidence_ids": list(map(str, evidence_ids)),
            }
        ],
        "remove_attributes": [],
    }


@pytest.mark.integration
def test_empty_profile_and_immutable_publication(client):
    http, admin, clock = client
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]
    assert base["facts"] == [] and base["version_number"] == 1
    consent(client)
    body = patch(base["version_id"])
    result = http.patch("/api/v1/profile", json=body, headers=headers(clock, key=str(uuid4())))
    assert result.status_code == 200
    profile = result.json()["data"]
    assert profile["version_number"] == 2 and profile["version_id"] != base["version_id"]
    assert profile["facts"][0]["value"] == body["changes"][0]["value"]
    assert profile["facts"][0]["provenance"] == "USER_CONFIRMED"
    assert [f["attribute"] for f in profile["facts"]] == ["education.gpa"]
    old = http.get("/api/v1/profile/versions/" + base["version_id"], headers=headers(clock))
    assert old.json()["data"] == base
    with admin.connect() as connection:
        event = connection.scalar(select(OutboxRecord.payload))
        assert event["profile_version_id"] == profile["version_id"]
        assert b"3.70" not in connection.scalar(select(IdempotencyRecord.response_ciphertext))


@pytest.mark.integration
def test_simultaneous_edits_yield_one_success_one_conflict(client):
    http, admin, clock = client
    consent(client)
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]

    def edit(_):
        return http.patch(
            "/api/v1/profile", json=patch(base), headers=headers(clock, key=str(uuid4()))
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, range(2)))
    assert sorted(r.status_code for r in results) == [200, 409]
    assert next(r for r in results if r.status_code == 409).json()["code"] == "VERSION_CONFLICT"
    with admin.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OutboxRecord)) == 1


@pytest.mark.integration
def test_encrypted_replay_is_exact_and_different_payload_conflicts(client):
    http, admin, clock = client
    consent(client)
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]
    key = str(uuid4())
    first = http.patch("/api/v1/profile", json=patch(base), headers=headers(clock, key=key))
    second = http.patch("/api/v1/profile", json=patch(base), headers=headers(clock, key=key))
    assert first.status_code == second.status_code == 200 and first.json() == second.json()
    assert second.headers["Idempotency-Replayed"] == "true"
    other = patch(base, value={"type": "GPA", "number": "3.00", "scale_max": "4.00"})
    conflict = http.patch("/api/v1/profile", json=other, headers=headers(clock, key=key))
    assert conflict.status_code == 409 and conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
    with admin.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(RunRecord)) == 1


@pytest.mark.integration
def test_pagination_newest_first_signed_and_owner_bound(client):
    http, _, clock = client
    consent(client)
    for _ in range(3):
        base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]
        assert (
            http.patch(
                "/api/v1/profile", json=patch(base), headers=headers(clock, key=str(uuid4()))
            ).status_code
            == 200
        )
    result = http.get("/api/v1/profile/versions?limit=2", headers=headers(clock)).json()["data"]
    assert [p["version_number"] for p in result["items"]] == [4, 3]
    cursor = result["next_cursor"]
    page = http.get(
        "/api/v1/profile/versions", params={"limit": 2, "cursor": cursor}, headers=headers(clock)
    )
    assert [p["version_number"] for p in page.json()["data"]["items"]] == [2, 1]
    for owner, value in [(accounts.SUBJECT, "broken"), (identity.OWNER_B, cursor)]:
        response = http.get(
            "/api/v1/profile/versions", params={"cursor": value}, headers=headers(clock, owner)
        )
        assert response.status_code == 400 and response.json()["code"] == "INVALID_CURSOR"


@pytest.mark.integration
def test_foreign_and_missing_history_indistinguishable(client):
    http, _, clock = client
    responses = [
        http.get("/api/v1/profile/versions/" + str(version), headers=headers(clock))
        for version in (identity.VERSION_B, uuid4())
    ]
    assert all(r.status_code == 404 and r.json()["code"] == "NOT_FOUND" for r in responses)


@pytest.mark.integration
def test_unknown_removal_and_original_gpa_scale(client):
    http, _, clock = client
    consent(client)
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]
    data = patch(base, value={"type": "GPA", "number": "3.50", "scale_max": "5.00"})
    data["changes"].append(
        {
            "attribute": "work_authorization.countries",
            "value": {"type": "UNKNOWN", "reason": "NOT_PROVIDED"},
            "evidence_ids": [],
        }
    )
    response = http.patch("/api/v1/profile", json=data, headers=headers(clock, key=str(uuid4())))
    facts = response.json()["data"]["facts"]
    assert (
        facts[0]["value"] == data["changes"][0]["value"] and facts[1]["value"]["type"] == "UNKNOWN"
    )
    removed = http.patch(
        "/api/v1/profile",
        json={
            "base_profile_version_id": response.json()["data"]["version_id"],
            "changes": [],
            "remove_attributes": ["work_authorization.countries"],
        },
        headers=headers(clock, key=str(uuid4())),
    )
    assert [f["attribute"] for f in removed.json()["data"]["facts"]] == ["education.gpa"]


@pytest.mark.integration
def test_matching_evidence_works_foreign_or_deleted_evidence_fails(client, evidence):
    http, admin, clock = client
    consent(client, identity.OWNER_A)
    consent(client, identity.OWNER_B)

    def edit(owner, value=True):
        base = http.get("/api/v1/profile", headers=headers(clock, owner)).json()["data"][
            "version_id"
        ]
        return http.patch(
            "/api/v1/profile",
            json=patch(
                base, "education.enrolled", {"type": "BOOLEAN", "value": value}, [evidence[2]]
            ),
            headers=headers(clock, owner, str(uuid4())),
        )

    assert (
        edit(identity.OWNER_B).status_code == 404
        and edit(identity.OWNER_A, False).status_code == 404
    )
    response = edit(identity.OWNER_A)
    assert response.status_code == 200
    version = response.json()["data"]["version_id"]
    assert response.json()["data"]["facts"][0]["provenance"] == "USER_CONFIRMED_DOCUMENT"
    with admin.begin() as connection:
        connection.execute(
            update(DocumentRecord)
            .where(DocumentRecord.id == evidence[0]["id"])
            .values(status="DELETING", deleted_at=clock.now(), revision=2)
        )
    old = http.get("/api/v1/profile/versions/" + version, headers=headers(clock, identity.OWNER_A))
    assert old.json()["data"]["facts"] == [] and edit(identity.OWNER_A).status_code == 404


@pytest.mark.integration
def test_consent_and_key_required(client):
    http, _, clock = client
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]
    assert (
        http.patch("/api/v1/profile", json=patch(base), headers=headers(clock)).status_code == 400
    )
    response = http.patch(
        "/api/v1/profile", json=patch(base), headers=headers(clock, key=str(uuid4()))
    )
    assert response.status_code == 403 and response.json()["code"] == "CONSENT_REQUIRED"


@pytest.mark.integration
@pytest.mark.parametrize(
    "value",
    [
        {"type": "GPA", "number": 3.7, "scale_max": "4.00"},
        {"type": "GPA", "number": "5.00", "scale_max": "4.00"},
        {"type": "BOOLEAN", "value": True},
    ],
)
def test_invalid_values_reject_without_mutation(client, value):
    http, admin, clock = client
    consent(client)
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]["version_id"]
    response = http.patch(
        "/api/v1/profile", json=patch(base, value=value), headers=headers(clock, key=str(uuid4()))
    )
    assert (
        response.status_code == 422
        and response.headers["content-type"] == "application/problem+json"
    )
    with admin.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(OutboxRecord)) == 0


@pytest.mark.integration
def test_outbox_failure_rolls_back_profile_and_replay(client, monkeypatch):
    from benefitbridge.profiles import service

    http, admin, clock = client
    consent(client)
    base = http.get("/api/v1/profile", headers=headers(clock)).json()["data"]
    original = service.OutboxRecord

    def fail(**values):
        return original(**{**values, "event_type": ""})

    monkeypatch.setattr(service, "OutboxRecord", fail)
    response = http.patch(
        "/api/v1/profile", json=patch(base["version_id"]), headers=headers(clock, key=str(uuid4()))
    )
    assert response.status_code == 503
    assert http.get("/api/v1/profile", headers=headers(clock)).json()["data"] == base
    with admin.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
