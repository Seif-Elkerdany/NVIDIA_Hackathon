"""MS-017 owner profile routes, composed from the verified account runtime."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Query, Request, Response
from fastapi.security import HTTPBearer

from benefitbridge.api.accounts import RESPONSES, AccountRoute, authenticate, get_runtime
from benefitbridge.config import ConfigurationError
from benefitbridge.domain.dto import Envelope, Page, Profile
from benefitbridge.domain.errors import DomainError
from benefitbridge.domain.requests import PatchProfile
from benefitbridge.ports import JobScope
from benefitbridge.profiles.service import ProfileService


@asynccontextmanager
async def lifecycle(app: FastAPI) -> AsyncIterator[None]:
    # Development can queue future MS-062 work; production must be able to consume it.
    if app.state.settings.app_env == "production":
        binding = app.state.dependencies.handlers.get("PROFILE_INVALIDATE")
        if binding is None or binding.scope != JobScope.PRIVATE:
            raise ConfigurationError("Production requires private PROFILE_INVALIDATE handler")
    yield


router = APIRouter(
    prefix="/api/v1",
    route_class=AccountRoute,
    dependencies=[Depends(HTTPBearer(auto_error=False))],
    lifespan=lifecycle,
)
ERRORS = {**RESPONSES, 409: RESPONSES[404]}


def service(request: Request) -> ProfileService:
    accounts = get_runtime(request).service
    secret = request.app.state.settings.receipt_encryption_key
    if secret is None:
        raise DomainError("DEPENDENCY_UNAVAILABLE", "Profile replay secret is unavailable.", 503)
    return ProfileService(
        accounts.private_sessions,
        accounts.clock,
        key=secret.get_secret_value().encode("utf-8"),
        notice_version=accounts.notice_version,
    )


def validate_request(request: Request, *, list_query: bool = False) -> None:
    names = tuple(request.query_params.keys())
    if names and (not list_query or any(name not in {"limit", "cursor"} for name in names)):
        raise DomainError("BAD_REQUEST", "Unexpected profile query parameters.", 400)
    if any(len(request.query_params.getlist(name)) != 1 for name in names):
        raise DomainError("BAD_REQUEST", "Duplicate query parameters.", 400)


@router.get(
    "/profile", operation_id="get_profile", response_model=Envelope[Profile], responses=ERRORS
)
async def get_profile(request: Request) -> Envelope[Profile]:
    validate_request(request)
    if await request.body():
        raise DomainError("BAD_REQUEST", "This operation accepts no body.", 400)
    identity = await authenticate(request)
    return Envelope(
        data=await service(request).get(identity.actor), request_id=request.state.request_id
    )


@router.patch(
    "/profile",
    operation_id="patch_profile",
    response_model=Envelope[Profile],
    responses=ERRORS,
    openapi_extra={
        "parameters": [
            {
                "name": "Idempotency-Key",
                "in": "header",
                "required": True,
                "schema": {
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 128,
                    "pattern": "^[!-~]+$",
                },
            }
        ]
    },
)
async def patch_profile(
    request: Request,
    response: Response,
    payload: PatchProfile,
) -> Envelope[Profile]:
    validate_request(request)
    # Missing required operation headers use the common 400 protocol error.
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key is None:
        raise DomainError("IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.", 400)
    if (
        len(request.headers.getlist("idempotency-key")) != 1
        or not 16 <= len(idempotency_key) <= 128
        or any(ord(char) < 33 or ord(char) > 126 for char in idempotency_key)
    ):
        raise DomainError("BAD_REQUEST", "Invalid idempotency key.", 400)
    identity = await authenticate(request)
    get_runtime(request).service.require_consent(identity.actor)
    result = await service(request).patch(identity.actor, payload, idempotency_key)
    if result.replayed:
        response.headers["Idempotency-Replayed"] = "true"
    return result.body


@router.get(
    "/profile/versions",
    operation_id="list_profile_versions",
    response_model=Envelope[Page[Profile]],
    responses=ERRORS,
)
async def list_profile_versions(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> Envelope[Page[Profile]]:
    validate_request(request, list_query=True)
    if await request.body():
        raise DomainError("BAD_REQUEST", "This operation accepts no body.", 400)
    identity = await authenticate(request)
    return Envelope(
        data=await service(request).list(identity.actor, limit=limit, cursor=cursor),
        request_id=request.state.request_id,
    )


@router.get(
    "/profile/versions/{profile_version_id}",
    operation_id="get_profile_version",
    response_model=Envelope[Profile],
    responses=ERRORS,
)
async def get_profile_version(request: Request, profile_version_id: UUID) -> Envelope[Profile]:
    validate_request(request)
    if await request.body():
        raise DomainError("BAD_REQUEST", "This operation accepts no body.", 400)
    identity = await authenticate(request)
    return Envelope(
        data=await service(request).get(identity.actor, profile_version_id),
        request_id=request.state.request_id,
    )
