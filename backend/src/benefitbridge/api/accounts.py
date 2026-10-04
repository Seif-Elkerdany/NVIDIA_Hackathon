"""MS-008 router, lifecycle composition and the shared safe API error boundary."""

import re
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx2 as httpx
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.security import HTTPBearer
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from starlette.responses import JSONResponse, Response

from benefitbridge.auth import (
    AccountService,
    AuthenticatedAccount,
    TokenVerifier,
    fetch_jwks,
    unauthenticated,
)
from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.domain.dto import Account, Envelope, FieldError, Problem
from benefitbridge.domain.errors import DomainError
from benefitbridge.domain.requests import PatchMe


@dataclass(frozen=True)
class AccountRuntime:
    verifier: TokenVerifier
    service: AccountService


async def validate_database_role(engine: AsyncEngine, *, identity: bool) -> None:
    group = "benefitbridge_identity_admin" if identity else "benefitbridge_app"
    predicate = "NOT (rolsuper OR rolbypassrls) AND pg_has_role(current_user, :group, 'member')"
    if not identity:
        predicate += " AND NOT pg_has_role(current_user, 'benefitbridge_identity_admin', 'member')"
    try:
        async with engine.connect() as connection:
            permitted = await connection.scalar(
                text(f"SELECT {predicate} FROM pg_catalog.pg_roles WHERE rolname = current_user"),
                {"group": group},
            )
    except SQLAlchemyError:
        raise ConfigurationError("Account database role verification failed") from None
    if not permitted:
        raise ConfigurationError("Account database credentials have incompatible privileges")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if isinstance(getattr(app.state, "account_runtime", None), AccountRuntime):
        yield
        return
    settings: Settings = app.state.settings
    if any(
        value is None
        for value in (
            settings.database_url,
            settings.identity_database_url,
            settings.jwt_issuer,
            settings.jwt_jwks_url,
            settings.deletion_hmac_key,
        )
    ):
        if settings.app_env == "production":
            raise ConfigurationError("Account API requires identity and JWT configuration")
        yield
        return
    assert settings.database_url and settings.identity_database_url
    assert settings.jwt_issuer and settings.jwt_jwks_url and settings.deletion_hmac_key
    if settings.jwt_issuer.scheme != "https" or settings.jwt_jwks_url.scheme != "https":
        raise ConfigurationError("Managed-auth issuer and JWKS must use HTTPS")
    private = create_async_engine(settings.database_url.get_secret_value(), hide_parameters=True)
    identity = create_async_engine(
        settings.identity_database_url.get_secret_value(), hide_parameters=True
    )
    try:
        await validate_database_role(private, identity=False)
        await validate_database_role(identity, identity=True)
    except ConfigurationError:
        await identity.dispose()
        await private.dispose()
        raise
    client = httpx.AsyncClient(timeout=5, follow_redirects=False, trust_env=False)
    clock = app.state.dependencies.clock

    async def keys() -> object:
        return await fetch_jwks(client, str(settings.jwt_jwks_url))

    app.state.account_runtime = AccountRuntime(
        TokenVerifier(str(settings.jwt_issuer), settings.jwt_audience, clock, keys),
        AccountService(
            async_sessionmaker(identity, expire_on_commit=False),
            async_sessionmaker(private, expire_on_commit=False),
            clock,
            settings.deletion_hmac_key.get_secret_value().encode("utf-8"),
            settings.processing_notice_version,
        ),
    )
    try:
        yield
    finally:
        await client.aclose()
        await identity.dispose()
        await private.dispose()
        del app.state.account_runtime


class AccountRoute(APIRoute):
    """Normalize validation and domain failures without echoing input or SQL errors."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            supplied = request.headers.get("X-Request-ID", "")
            request.state.request_id = (
                supplied if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied) else str(uuid4())
            )
            try:
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 256 * 1024:
                        raise DomainError(
                            "PAYLOAD_TOO_LARGE", "Request body exceeds its limit.", 413
                        )
                    body.extend(chunk)
                request._body = bytes(body)
                if (
                    request.method == "PATCH"
                    and request.headers.get("content-type", "").split(";")[0].strip().lower()
                    != "application/json"
                ):
                    raise DomainError("BAD_REQUEST", "JSON content type is required.", 400)
                response = await handler(request)
            except RequestValidationError as error:
                fields = tuple(
                    FieldError(
                        path=".".join(str(part) for part in item["loc"]), message="Invalid value."
                    )
                    for item in error.errors()
                )
                response = problem_response(
                    request,
                    DomainError(
                        "VALIDATION_ERROR", "Request validation failed.", 422, field_errors=fields
                    ),
                )
            except DomainError as error:
                response = problem_response(request, error)
            except SQLAlchemyError:
                response = problem_response(
                    request,
                    DomainError(
                        "DEPENDENCY_UNAVAILABLE", "Account storage is unavailable.", 503, True
                    ),
                )
            response.headers["X-Request-ID"] = request.state.request_id
            response.headers["Cache-Control"] = "no-store"
            return response

        return handle


def problem_response(request: Request, error: DomainError) -> JSONResponse:
    problem = Problem(
        type="urn:benefitbridge:problem:" + error.code.lower().replace("_", "-"),
        title=error.code.replace("_", " ").capitalize(),
        status=error.status,
        detail=error.safe_message,
        code=error.code,
        request_id=request.state.request_id,
        errors=error.field_errors,
        retryable=error.retryable,
    )
    return JSONResponse(
        problem.model_dump(mode="json"),
        status_code=error.status,
        media_type="application/problem+json",
        headers={"WWW-Authenticate": "Bearer"} if error.status == 401 else None,
    )


def get_runtime(request: Request) -> AccountRuntime:
    runtime = getattr(request.app.state, "account_runtime", None)
    if not isinstance(runtime, AccountRuntime):
        raise DomainError("DEPENDENCY_UNAVAILABLE", "Account service is unavailable.", 503, True)
    return runtime


async def authenticate(request: Request) -> AuthenticatedAccount:
    headers = request.headers.getlist("authorization")
    if len(headers) != 1:
        raise unauthenticated()
    scheme, separator, token = headers[0].partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or token.strip() != token:
        raise unauthenticated()
    runtime = get_runtime(request)
    owner = await runtime.verifier.verify(token)
    identity = await runtime.service.bootstrap(owner, request.state.request_id)
    request.state.actor = identity.actor
    return identity


RESPONSES: dict[int | str, dict[str, object]] = {
    status: {
        "model": Problem,
        "content": {
            "application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}
        },
    }
    for status in (400, 401, 403, 404, 413, 422, 503)
}
router = APIRouter(
    prefix="/api/v1",
    route_class=AccountRoute,
    lifespan=lifespan,
    dependencies=[Depends(HTTPBearer(auto_error=False))],
)


@router.get("/me", operation_id="get_me", response_model=Envelope[Account], responses=RESPONSES)
async def get_me(request: Request) -> Envelope[Account]:
    if request.query_params or await request.body():
        raise DomainError("BAD_REQUEST", "This operation accepts no query or body.", 400)
    identity = await authenticate(request)
    return Envelope(data=identity.account, request_id=request.state.request_id)


@router.patch("/me", operation_id="patch_me", response_model=Envelope[Account], responses=RESPONSES)
async def patch_me(request: Request, payload: PatchMe) -> Envelope[Account]:
    if request.query_params:
        raise DomainError("BAD_REQUEST", "This operation accepts no query parameters.", 400)
    identity = await authenticate(request)
    account = await get_runtime(request).service.patch(identity.actor, payload)
    return Envelope(data=account, request_id=request.state.request_id)
