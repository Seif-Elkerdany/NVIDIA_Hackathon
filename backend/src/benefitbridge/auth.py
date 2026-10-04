"""Managed-auth verification and identity persistence; no token or private-data logs."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC
from json import JSONDecodeError
from uuid import UUID, uuid4

import httpx2 as httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from benefitbridge.db.base import owner_transaction, subject_hmac
from benefitbridge.db.profiles import AccountRecord, ProfileRecord, ProfileVersionRecord
from benefitbridge.domain.dto import Account, Consent
from benefitbridge.domain.enums import AccountStatus
from benefitbridge.domain.errors import DomainError
from benefitbridge.domain.requests import PatchMe
from benefitbridge.ports import ActorContext, Clock

ALGORITHMS = ("RS256", "ES256")
JWKS_TTL_SECONDS = 300
JWKS_REFRESH_INTERVAL = 30
MAX_JWKS_BYTES = 65536
MAX_JWKS_KEYS = 32
MAX_TOKEN_BYTES = 16384
JwksFetch = Callable[[], Awaitable[object]]


def unauthenticated() -> DomainError:
    return DomainError("UNAUTHENTICATED", "Authentication is required.", 401)


async def fetch_jwks(client: httpx.AsyncClient, url: str) -> object:
    """Configured HTTPS endpoint only; no JWT-provided URL, redirects or unbounded body."""
    try:
        async with client.stream("GET", url, timeout=5, follow_redirects=False) as response:
            response.raise_for_status()
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > MAX_JWKS_BYTES:
                    raise ValueError("JWKS exceeds its size limit")
            import json

            return json.loads(body)
    except (httpx.HTTPError, ValueError, JSONDecodeError):
        raise DomainError(
            "DEPENDENCY_UNAVAILABLE", "Authentication keys are unavailable.", 503, True
        ) from None


class TokenVerifier:
    """Bounded, coalesced issuer-key cache with an injected clock for all claim checks."""

    def __init__(self, issuer: str, audience: str, clock: Clock, fetch: JwksFetch) -> None:
        self.issuer, self.audience, self.clock, self.fetch = issuer, audience, clock, fetch
        self._keys: dict[str, jwt.PyJWK] = {}
        self._expires = float("-inf")
        self._refresh_after = float("-inf")
        self._lock = asyncio.Lock()

    def clear_cache(self) -> None:
        """Operator hook for signing-key revocation; refresh throttling still applies."""
        self._keys.clear()
        self._expires = float("-inf")

    async def _key(self, kid: str, algorithm: str) -> jwt.PyJWK:
        async with self._lock:
            now = self.clock.monotonic()
            if (now >= self._expires or kid not in self._keys) and now >= self._refresh_after:
                self._refresh_after = now + JWKS_REFRESH_INTERVAL
                try:
                    document = await asyncio.wait_for(self.fetch(), timeout=5)
                except TimeoutError:
                    raise DomainError(
                        "DEPENDENCY_UNAVAILABLE", "Authentication keys are unavailable.", 503, True
                    ) from None
                try:
                    if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
                        raise ValueError("Invalid JWKS")
                    raw_keys = document["keys"]
                    if not 1 <= len(raw_keys) <= MAX_JWKS_KEYS:
                        raise ValueError("Invalid JWKS key count")
                    keys: dict[str, jwt.PyJWK] = {}
                    for raw in raw_keys:
                        if not isinstance(raw, dict):
                            raise ValueError("Invalid signing key")
                        key_id, alg = raw.get("kid"), raw.get("alg")
                        if alg not in ALGORITHMS:
                            continue
                        if (
                            not isinstance(key_id, str)
                            or not 1 <= len(key_id) <= 128
                            or key_id in keys
                            or raw.get("use", "sig") != "sig"
                            or "d" in raw
                            or ("key_ops" in raw and raw["key_ops"] != ["verify"])
                        ):
                            raise ValueError("Invalid signing key")
                        key = jwt.PyJWK.from_dict(raw, algorithm=alg)
                        if alg == "RS256" and (
                            not isinstance(key.key, rsa.RSAPublicKey) or key.key.key_size < 2048
                        ):
                            raise ValueError("Invalid RSA key")
                        if alg == "ES256" and (
                            not isinstance(key.key, ec.EllipticCurvePublicKey)
                            or not isinstance(key.key.curve, ec.SECP256R1)
                        ):
                            raise ValueError("Invalid EC key")
                        keys[key_id] = key
                    if not keys:
                        raise ValueError("No accepted signing keys")
                except (ValueError, jwt.PyJWTError):
                    raise DomainError(
                        "DEPENDENCY_UNAVAILABLE", "Authentication keys are unavailable.", 503, True
                    ) from None
                self._keys = keys
                self._expires = now + JWKS_TTL_SECONDS
            if now >= self._expires:
                raise DomainError(
                    "DEPENDENCY_UNAVAILABLE", "Authentication keys are unavailable.", 503, True
                )
            cached_key = self._keys.get(kid)
            if cached_key is None or cached_key.algorithm_name != algorithm:
                raise unauthenticated()
            return cached_key

    async def verify(self, token: str) -> UUID:
        if len(token) > MAX_TOKEN_BYTES or token.count(".") != 2:
            raise unauthenticated()
        try:
            header = jwt.get_unverified_header(token)
            alg, kid = header.get("alg"), header.get("kid")
            if alg not in ALGORITHMS or not isinstance(kid, str) or not 1 <= len(kid) <= 128:
                raise unauthenticated()
            if any(name in header for name in ("crit", "jku", "jwk", "x5u", "b64")):
                raise unauthenticated()
            key = await self._key(kid, alg)
            claims = jwt.decode(
                token,
                key,
                algorithms=list(ALGORITHMS),
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "require": ["sub", "iss", "aud", "exp", "iat"],
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                },
            )
            now = self.clock.now().timestamp()
            exp, iat, nbf = claims["exp"], claims["iat"], claims.get("nbf", claims["iat"])
            if any(type(value) is not int for value in (exp, iat, nbf)):
                raise unauthenticated()
            if exp <= now or iat > now or nbf > now or exp <= iat:
                raise unauthenticated()
            if claims.get("role", "authenticated") != "authenticated":
                raise unauthenticated()
            owner = UUID(claims["sub"])
            if owner.version is None or owner.int == 0:
                raise unauthenticated()
            return owner
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            raise unauthenticated() from None


@dataclass(frozen=True)
class AuthenticatedAccount:
    account: Account
    actor: ActorContext


def account_dto(row: AccountRecord) -> Account:
    return Account(
        id=row.id,
        display_name=row.display_name,
        timezone=row.timezone,
        status=row.status,
        consent=None
        if row.consent_at is None
        else Consent(version=row.consent_version, accepted_at=row.consent_at.astimezone(UTC)),
        is_demo=row.is_demo,
        created_at=row.created_at.astimezone(UTC),
    )


class AccountService:
    """Identity sessions bootstrap only; ordinary mutations use owner-filtered RLS sessions."""

    def __init__(
        self,
        identity_sessions: async_sessionmaker[AsyncSession],
        private_sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        deletion_key: bytes,
        notice_version: str,
    ) -> None:
        self.identity_sessions, self.private_sessions = identity_sessions, private_sessions
        self.clock, self.deletion_key, self.notice_version = clock, deletion_key, notice_version

    async def _denied(self, session: AsyncSession, owner: UUID) -> None:
        denied = await session.scalar(
            text("SELECT public.benefitbridge_subject_denied(:digest, :at)"),
            {"digest": subject_hmac(owner, self.deletion_key), "at": self.clock.now()},
        )
        if denied:
            raise unauthenticated()

    async def bootstrap(self, owner: UUID, request_id: str) -> AuthenticatedAccount:
        async with self.identity_sessions() as session, session.begin():
            permitted = await session.scalar(
                text("""SELECT NOT (rolsuper OR rolbypassrls)
                AND pg_has_role(current_user, 'benefitbridge_identity_admin', 'member')
                FROM pg_catalog.pg_roles WHERE rolname = current_user""")
            )
            if not permitted:
                raise DomainError(
                    "DEPENDENCY_UNAVAILABLE", "Identity service is misconfigured.", 503, True
                )
            # An absent account cannot be row-locked; this subject-scoped lock
            # serializes first login without a race or an abandoned partial profile.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:subject, 0))"),
                {"subject": str(owner)},
            )
            row = (
                await session.execute(
                    select(AccountRecord).where(AccountRecord.id == owner).with_for_update()
                )
            ).scalar_one_or_none()
            # Check after the account lock: a concurrent purge may have removed
            # the row while we waited, leaving only its committed deny marker.
            await self._denied(session, owner)
            if row is not None and row.status != AccountStatus.ACTIVE:
                raise unauthenticated()
            if row is None:
                now = self.clock.now()
                row = AccountRecord(
                    id=owner,
                    status=AccountStatus.ACTIVE,
                    display_name="Applicant",
                    timezone="UTC",
                    created_at=now,
                    is_demo=False,
                    deletion_epoch=0,
                    consent_version=None,
                    consent_at=None,
                )
                session.add(row)
                await session.flush()
                profile_id, version_id = uuid4(), uuid4()
                session.add(
                    ProfileRecord(id=profile_id, owner_id=owner, current_version_id=version_id)
                )
                await session.flush()
                session.add(
                    ProfileVersionRecord(
                        id=version_id, owner_id=owner, version_number=1, created_at=now
                    )
                )
                await session.flush()
            return AuthenticatedAccount(
                account_dto(row),
                ActorContext(owner, row.deletion_epoch, request_id, row.consent_version),
            )

    async def patch(self, actor: ActorContext, patch: PatchMe) -> Account:
        if patch.consent_version is not None and patch.consent_version != self.notice_version:
            raise DomainError(
                "VALIDATION_ERROR", "Consent version does not match the current notice.", 422
            )
        async with owner_transaction(self.private_sessions, actor) as session:
            await self._denied(session, actor.owner_id)
            row = (
                await session.execute(
                    select(AccountRecord).where(AccountRecord.id == actor.owner_id)
                )
            ).scalar_one()
            if patch.display_name is not None:
                row.display_name = patch.display_name
            if patch.timezone is not None:
                row.timezone = patch.timezone
            if patch.consent_version is not None and row.consent_version != patch.consent_version:
                row.consent_version, row.consent_at = patch.consent_version, self.clock.now()
            await session.flush()
            return account_dto(row)

    def require_consent(self, actor: ActorContext) -> None:
        if actor.consent_version != self.notice_version:
            raise DomainError("CONSENT_REQUIRED", "Current processing consent is required.", 403)
