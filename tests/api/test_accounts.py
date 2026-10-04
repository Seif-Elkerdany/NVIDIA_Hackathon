"""Synthetic signed credentials, injected clocks/JWKS and real PostgreSQL account isolation."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID

import httpx2 as httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tests.fakes.providers import FakeClock
from tests.integration import test_identity as identity_fixtures

from benefitbridge.api.accounts import AccountRuntime, validate_database_role
from benefitbridge.auth import AccountService, TokenVerifier, fetch_jwks
from benefitbridge.composition import Dependencies
from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.db.base import subject_hmac
from benefitbridge.domain.errors import DomainError
from benefitbridge.main import create_app
from benefitbridge.ports import ActorContext

database = identity_fixtures.database

ISSUER = "https://synthetic.example.invalid/auth/v1"
SUBJECT = UUID("00000000-0000-4000-8000-000000000099")
KEY = ec.derive_private_key(7, ec.SECP256R1())
DELETION_KEY = b"synthetic-account-deletion-key-000"


def jwk(kid="synthetic-key", key=KEY):
    return {
        **jwt.algorithms.ECAlgorithm.to_jwk(key.public_key(), as_dict=True),
        "kid": kid,
        "alg": "ES256",
        "use": "sig",
    }


def token(clock, changes=None, key=KEY, headers=None):
    now = int(clock.now().timestamp())
    claims = {
        "sub": str(SUBJECT),
        "iss": ISSUER,
        "aud": "authenticated",
        "iat": now - 1,
        "exp": now + 600,
        "role": "authenticated",
    }
    claims.update(changes or {})
    return jwt.encode(claims, key, algorithm="ES256", headers=headers or {"kid": "synthetic-key"})


def run(coroutine):
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)


def verifier(clock, keys=None):
    async def fetch():
        return {"keys": keys or [jwk()]}

    return TokenVerifier(ISSUER, "authenticated", clock, fetch)


def test_valid_signed_token_uses_injected_clock_not_machine_time(fake_clock):
    verify = verifier(fake_clock)
    assert run(verify.verify(token(fake_clock))) == SUBJECT
    fake_clock.advance(600)
    with pytest.raises(DomainError) as error:
        run(verify.verify(token(FakeClock())))
    assert error.value.status == 401


def test_rsa_signature_uses_the_same_fixed_algorithm_policy(fake_clock):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    raw_key = {
        **jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True),
        "kid": "rsa",
        "alg": "RS256",
        "use": "sig",
    }
    now = int(fake_clock.now().timestamp())
    signed = jwt.encode(
        {
            "sub": str(SUBJECT),
            "iss": ISSUER,
            "aud": "authenticated",
            "iat": now - 1,
            "exp": now + 60,
        },
        key,
        algorithm="RS256",
        headers={"kid": "rsa"},
    )
    assert run(verifier(fake_clock, [raw_key]).verify(signed)) == SUBJECT


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://other.example.invalid/auth/v1"},
        {"aud": "other-project"},
        {"exp": 1},
        {"exp": True},
        {"exp": "9999999999"},
        {"sub": "not-an-id"},
        {"role": "service_role"},
        {"nbf": 9999999999},
        {"iat": 9999999999},
    ],
)
def test_untrusted_claims_fail(fake_clock, changes):
    with pytest.raises(DomainError) as error:
        run(verifier(fake_clock).verify(token(fake_clock, changes)))
    assert error.value.code == "UNAUTHENTICATED"


def test_signature_algorithm_and_token_header_urls_are_not_trusted(fake_clock):
    signed = token(fake_clock, key=ec.derive_private_key(8, ec.SECP256R1()))
    for raw in (
        signed,
        "invalid",
        token(fake_clock, headers={"kid": "synthetic-key", "jku": "https://attacker.invalid/keys"}),
        jwt.encode(
            {"sub": str(SUBJECT)},
            "synthetic-hmac-key-at-least-32-bytes",
            algorithm="HS256",
            headers={"kid": "synthetic-key"},
        ),
    ):
        with pytest.raises(DomainError) as error:
            run(verifier(fake_clock).verify(raw))
        assert error.value.status == 401


def test_jwks_rotation_expiry_and_unknown_kid_refresh_are_bounded(fake_clock):
    calls = []
    keys = [jwk()]

    async def fetch():
        calls.append(1)
        return {"keys": keys}

    verify = TokenVerifier(ISSUER, "authenticated", fake_clock, fetch)

    async def scenario():
        await asyncio.gather(*(verify.verify(token(fake_clock)) for _ in range(10)))
        assert len(calls) == 1
        for index in range(20):
            with pytest.raises(DomainError):
                await verify.verify(token(fake_clock, headers={"kid": f"unknown-{index}"}))
        assert len(calls) == 1
        fake_clock.advance(30)
        keys.append(jwk("rotated"))
        assert await verify.verify(token(fake_clock, headers={"kid": "rotated"})) == SUBJECT
        assert len(calls) == 2
        fake_clock.advance(300)
        keys[:] = [jwk("rotated")]
        with pytest.raises(DomainError):
            await verify.verify(token(fake_clock))
        assert len(calls) == 3

    run(scenario())


@pytest.mark.parametrize(
    "keys",
    [
        [jwk(), jwk()],
        [jwk(str(i)) for i in range(33)],
        [{"kid": "bad", "alg": "ES256", "kty": "EC"}],
    ],
)
def test_invalid_key_sets_fail_closed(fake_clock, keys):
    with pytest.raises(DomainError) as error:
        run(verifier(fake_clock, keys).verify(token(fake_clock)))
    assert error.value.status == 503


def test_jwks_fetch_bounds_body_and_refuses_redirects():
    for response in (
        httpx.Response(302, headers={"Location": "https://attacker.invalid"}),
        httpx.Response(200, content=b"x" * 65537),
        httpx.Response(200, content=b"invalid-json"),
    ):

        async def scenario(response=response):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(lambda _: response)
            ) as client:
                with pytest.raises(DomainError) as error:
                    await fetch_jwks(client, ISSUER + "/.well-known/jwks.json")
                assert error.value.status == 503

        run(scenario())


@pytest.fixture
def account_client(database, fake_clock):
    admin, app_engine, app_url, identity_url = database
    app_engine.dispose()

    async def sessions():
        return create_async_engine(identity_url), create_async_engine(app_url)

    identity, private = run(sessions())
    service = AccountService(
        async_sessionmaker(identity, expire_on_commit=False),
        async_sessionmaker(private, expire_on_commit=False),
        fake_clock,
        DELETION_KEY,
        "2026-10-01",
    )
    app = create_app(Settings(_env_file=None, app_env="test"))
    app.state.account_runtime = AccountRuntime(verifier(fake_clock), service)
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as client:
        yield client, service, admin, fake_clock
    run(identity.dispose())
    run(private.dispose())


@pytest.mark.integration
def test_account_bootstrap_is_atomic_and_concurrent(account_client):
    client, _, admin, clock = account_client
    bearer = {"Authorization": "Bearer " + token(clock), "X-Request-ID": "synthetic-request"}
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: client.get("/api/v1/me", headers=bearer), range(8)))
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json() == responses[0].json() for response in responses)
    assert responses[0].json()["data"]["consent"] is None
    assert responses[0].headers["cache-control"] == "no-store"
    assert responses[0].headers["x-request-id"] == "synthetic-request"
    with admin.connect() as connection:
        for table in ("accounts", "profiles", "profile_versions"):
            assert (
                connection.scalar(
                    text(
                        f"SELECT count(*) FROM {table} WHERE "
                        + ("id" if table == "accounts" else "owner_id")
                        + " = :owner"
                    ),
                    {"owner": SUBJECT},
                )
                == 1
            )
        assert (
            connection.scalar(
                text("SELECT count(*) FROM profile_version_facts WHERE owner_id = :owner"),
                {"owner": SUBJECT},
            )
            == 0
        )


@pytest.mark.integration
def test_patch_persists_preferences_consent_and_replay_timestamp(account_client):
    client, service, admin, clock = account_client
    headers = {"Authorization": "Bearer " + token(clock)}
    response = client.patch(
        "/api/v1/me",
        headers=headers,
        json={
            "display_name": "Synthetic Applicant",
            "timezone": "Africa/Cairo",
            "consent_version": "2026-10-01",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["timezone"] == "Africa/Cairo"
    assert data["display_name"] == "Synthetic Applicant"
    assert data["consent"]["accepted_at"] == clock.now().isoformat().replace("+00:00", "Z")
    clock.advance(1)
    replay = client.patch("/api/v1/me", headers=headers, json={"consent_version": "2026-10-01"})
    assert replay.json()["data"]["consent"] == data["consent"]
    service.require_consent(ActorContext(SUBJECT, 0, "synthetic", "2026-10-01"))
    with pytest.raises(DomainError) as error:
        service.require_consent(ActorContext(SUBJECT, 0, "synthetic"))
    assert error.value.code == "CONSENT_REQUIRED"
    with admin.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT display_name FROM accounts WHERE id = :owner"), {"owner": SUBJECT}
            )
            == "Synthetic Applicant"
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"owner_id": str(SUBJECT)},
        {"status": "ACTIVE"},
        {"timezone": "invalid/zone"},
        {"display_name": None},
        {"consent_version": "old"},
    ],
)
def test_invalid_patch_uses_safe_problem_contract(account_client, payload):
    client, _, _, clock = account_client
    response = client.patch(
        "/api/v1/me", headers={"Authorization": "Bearer " + token(clock)}, json=payload
    )
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "invalid/zone" not in response.text


@pytest.mark.integration
def test_expired_wrong_issuer_tombstone_and_deny_ledger_fail(account_client):
    client, _, admin, clock = account_client
    for changes in ({"exp": 1}, {"iss": "https://other.invalid"}):
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token(clock, changes)}
        )
        assert response.status_code == 401
    headers = {"Authorization": "Bearer " + token(clock)}
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    with admin.begin() as connection:
        connection.execute(
            text("UPDATE accounts SET status = 'DELETING', deletion_epoch = 1 WHERE id = :owner"),
            {"owner": SUBJECT},
        )
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    with admin.begin() as connection:
        connection.execute(
            text("INSERT INTO deleted_subjects VALUES (:digest, :now, :until)"),
            {
                "digest": subject_hmac(SUBJECT, DELETION_KEY),
                "now": clock.now(),
                "until": clock.now() + timedelta(days=31),
            },
        )
        connection.execute(text("DELETE FROM accounts WHERE id = :owner"), {"owner": SUBJECT})
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    assert (
        client.patch("/api/v1/me", headers=headers, json={"display_name": "Recreated"}).status_code
        == 401
    )
    with admin.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM accounts WHERE id = :owner"), {"owner": SUBJECT}
            )
            == 0
        )


def test_missing_configuration_and_invalid_protocol_do_not_become_fakes():
    with TestClient(create_app(Settings(_env_file=None, app_env="test"))) as client:
        for headers in ({}, {"Authorization": "Basic synthetic"}):
            response = client.get("/api/v1/me", headers=headers)
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "Bearer"
        assert (
            client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic"}).status_code
            == 503
        )
        assert client.patch("/api/v1/me", content=b"x" * (256 * 1024 + 1)).status_code == 413


@pytest.mark.integration
def test_bootstrap_database_failure_rolls_back_account_and_profile(account_client, monkeypatch):
    from benefitbridge import auth

    client, _, admin, clock = account_client
    original = auth.uuid4
    monkeypatch.setattr(auth, "uuid4", lambda: identity_fixtures.VERSION_A)
    headers = {"Authorization": "Bearer " + token(clock)}
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    with admin.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM accounts WHERE id = :owner"), {"owner": SUBJECT}
            )
            == 0
        )
        assert (
            connection.scalar(
                text("SELECT count(*) FROM profiles WHERE owner_id = :owner"), {"owner": SUBJECT}
            )
            == 0
        )
    monkeypatch.setattr(auth, "uuid4", original)
    assert client.get("/api/v1/me", headers=headers).status_code == 200


@pytest.mark.integration
def test_router_lifespan_binds_real_database_sessions(database, fake_clock, monkeypatch):
    _, app_engine, app_url, identity_url = database
    app_engine.dispose()
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"keys": [jwk()]})),
        ),
    )
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=app_url.render_as_string(hide_password=False),
        identity_database_url=identity_url.render_as_string(hide_password=False),
        jwt_issuer=ISSUER,
        jwt_jwks_url=ISSUER + "/.well-known/jwks.json",
        deletion_hmac_key=DELETION_KEY.decode(),
    )
    app = create_app(settings)
    app.state.dependencies = Dependencies(clock=fake_clock)
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as client:
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token(fake_clock)}
        )
        assert response.status_code == 200
        assert response.json()["data"]["id"] == str(SUBJECT)
    assert not hasattr(app.state, "account_runtime")


@pytest.mark.integration
def test_runtime_role_checks_reject_bypass_and_swapped_credentials(database):
    admin, app_engine, app_url, identity_url = database
    app_engine.dispose()

    async def check(url, identity):
        engine = create_async_engine(url)
        try:
            await validate_database_role(engine, identity=identity)
        finally:
            await engine.dispose()

    for url, identity in ((admin.url, False), (identity_url, False), (app_url, True)):
        with pytest.raises(ConfigurationError, match="incompatible privileges"):
            run(check(url, identity))
