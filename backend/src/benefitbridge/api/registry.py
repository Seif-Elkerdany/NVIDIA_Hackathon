"""Ordered API allowlist and fail-closed production composition (design section 1)."""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib import import_module
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse, Response

from benefitbridge.composition import Dependencies, build_dependencies
from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.domain.dto import Problem
from benefitbridge.domain.enums import RunKind
from benefitbridge.ports import JobScope


@dataclass(frozen=True)
class RouterSpec:
    module: str
    operations: tuple[str, ...]
    handlers: tuple[str, ...] = ()
    feature: str | None = None


# These modules are the API ownership boundaries in sprints.md/API.md.
# Handler IDs are entrypoints named by RunKind; modules additionally declare
# required_handlers for their intermediate stages and public maintenance hooks.
ROUTER_SPECS: tuple[RouterSpec, ...] = (
    RouterSpec("accounts", ("get_me", "patch_me")),
    RouterSpec(
        "profiles", ("get_profile", "patch_profile", "list_profile_versions", "get_profile_version")
    ),
    RouterSpec(
        "documents",
        (
            "create_document_upload",
            "put_document_content",
            "complete_document_upload",
            "list_documents",
            "get_document",
            "get_document_download",
        ),
        (RunKind.DOCUMENT_PARSE,),
    ),
    RouterSpec("facts", ("list_fact_candidates", "review_fact_candidates", "get_evidence")),
    RouterSpec("runs", ("list_runs", "get_run", "cancel_run", "get_run_events")),
    RouterSpec(
        "opportunities",
        ("list_opportunities", "get_opportunity", "get_opportunity_version", "get_requirements"),
    ),
    RouterSpec("sources", ("get_source",)),
    RouterSpec(
        "discovery", ("start_discovery", "import_opportunity"), (RunKind.DISCOVERY, RunKind.IMPORT)
    ),
    RouterSpec("evaluations", ("start_evaluation", "get_evaluation"), (RunKind.EVALUATE,)),
    RouterSpec("clarifications", ("get_clarifications", "answer_clarifications")),
    RouterSpec("saved", ("list_saved", "save_opportunity", "delete_saved")),
    RouterSpec(
        "applications",
        ("list_applications", "create_application", "get_application", "patch_checklist_item"),
    ),
    RouterSpec(
        "drafts",
        ("start_draft", "get_draft", "edit_draft", "accept_draft", "export_application"),
        (RunKind.DRAFT_GENERATE, RunKind.DRAFT_VALIDATE),
    ),
    RouterSpec("refresh", ("refresh_opportunity",), (RunKind.REFRESH,)),
    RouterSpec("document_delete", ("delete_document",), (RunKind.DOCUMENT_DELETE,)),
    RouterSpec(
        "account_delete", ("delete_account", "get_deletion_receipt"), (RunKind.ACCOUNT_DELETE,)
    ),
    RouterSpec("usage", ("get_usage", "get_capabilities")),
    RouterSpec("health", ("health_live", "health_ready")),
    RouterSpec("demo", ("reset_demo",), (RunKind.DEMO_RESET,), "demo"),
    RouterSpec(
        "watch",
        (
            "list_watches",
            "create_watch",
            "patch_watch",
            "delete_watch",
            "list_notifications",
            "read_notification",
        ),
        feature="watch",
    ),
)


# Stable operation IDs and transports from API.md; no runtime file discovery.
OPERATION_CONTRACTS: dict[str, tuple[str, str]] = {
    "get_me": ("GET", "/api/v1/me"),
    "patch_me": ("PATCH", "/api/v1/me"),
    "get_profile": ("GET", "/api/v1/profile"),
    "patch_profile": ("PATCH", "/api/v1/profile"),
    "list_profile_versions": ("GET", "/api/v1/profile/versions"),
    "get_profile_version": ("GET", "/api/v1/profile/versions/{profile_version_id}"),
    "create_document_upload": ("POST", "/api/v1/documents/uploads"),
    "put_document_content": ("PUT", "/api/v1/documents/{document_id}/content"),
    "complete_document_upload": ("POST", "/api/v1/documents/{document_id}/complete"),
    "list_documents": ("GET", "/api/v1/documents"),
    "get_document": ("GET", "/api/v1/documents/{document_id}"),
    "get_document_download": ("GET", "/api/v1/documents/{document_id}/download"),
    "delete_document": ("DELETE", "/api/v1/documents/{document_id}"),
    "list_fact_candidates": ("GET", "/api/v1/fact-candidates"),
    "review_fact_candidates": ("POST", "/api/v1/fact-candidates/reviews"),
    "get_evidence": ("GET", "/api/v1/evidence/{evidence_id}"),
    "start_discovery": ("POST", "/api/v1/discovery-runs"),
    "import_opportunity": ("POST", "/api/v1/opportunity-imports"),
    "list_runs": ("GET", "/api/v1/runs"),
    "get_run": ("GET", "/api/v1/runs/{run_id}"),
    "cancel_run": ("POST", "/api/v1/runs/{run_id}/cancel"),
    "get_run_events": ("GET", "/api/v1/runs/{run_id}/events"),
    "get_clarifications": ("GET", "/api/v1/runs/{run_id}/clarifications"),
    "answer_clarifications": (
        "POST",
        "/api/v1/runs/{run_id}/clarifications/{clarification_set_id}/answers",
    ),
    "list_opportunities": ("GET", "/api/v1/opportunities"),
    "get_opportunity": ("GET", "/api/v1/opportunities/{opportunity_id}"),
    "get_opportunity_version": (
        "GET",
        "/api/v1/opportunities/{opportunity_id}/versions/{opportunity_version_id}",
    ),
    "get_requirements": ("GET", "/api/v1/requirement-sets/{requirement_set_id}"),
    "get_source": ("GET", "/api/v1/sources/{source_snapshot_id}"),
    "start_evaluation": ("POST", "/api/v1/evaluations"),
    "get_evaluation": ("GET", "/api/v1/evaluations/{evaluation_id}"),
    "refresh_opportunity": ("POST", "/api/v1/opportunities/{opportunity_id}/refresh"),
    "list_saved": ("GET", "/api/v1/saved-opportunities"),
    "save_opportunity": ("PUT", "/api/v1/saved-opportunities/{opportunity_id}"),
    "delete_saved": ("DELETE", "/api/v1/saved-opportunities/{opportunity_id}"),
    "list_applications": ("GET", "/api/v1/applications"),
    "create_application": ("POST", "/api/v1/applications"),
    "get_application": ("GET", "/api/v1/applications/{application_id}"),
    "patch_checklist_item": ("PATCH", "/api/v1/applications/{application_id}/items/{item_id}"),
    "start_draft": ("POST", "/api/v1/applications/{application_id}/drafts"),
    "get_draft": ("GET", "/api/v1/drafts/{draft_id}"),
    "edit_draft": ("POST", "/api/v1/drafts/{draft_id}/versions"),
    "accept_draft": ("POST", "/api/v1/drafts/{draft_id}/accept"),
    "export_application": ("GET", "/api/v1/applications/{application_id}/export"),
    "get_usage": ("GET", "/api/v1/usage"),
    "delete_account": ("DELETE", "/api/v1/me"),
    "get_deletion_receipt": ("GET", "/api/v1/deletion-receipts/{receipt_id}"),
    "health_live": ("GET", "/api/v1/health/live"),
    "health_ready": ("GET", "/api/v1/health/ready"),
    "get_capabilities": ("GET", "/api/v1/capabilities"),
    "reset_demo": ("POST", "/api/v1/demo/reset"),
    "list_watches": ("GET", "/api/v1/watches"),
    "create_watch": ("POST", "/api/v1/watches"),
    "patch_watch": ("PATCH", "/api/v1/watches/{watch_id}"),
    "delete_watch": ("DELETE", "/api/v1/watches/{watch_id}"),
    "list_notifications": ("GET", "/api/v1/notifications"),
    "read_notification": ("PUT", "/api/v1/notifications/{notification_id}/read"),
}


@dataclass(frozen=True)
class LoadedRouter:
    spec: RouterSpec
    router: APIRouter
    required_handlers: tuple[str, ...]


def _enabled(spec: RouterSpec, settings: Settings) -> bool:
    return (
        spec.feature is None
        or (spec.feature == "demo" and settings.demo_enabled)
        or (spec.feature == "watch" and settings.watch_enabled)
    )


def load_routers(settings: Settings) -> tuple[LoadedRouter, ...]:
    """Only a genuinely absent allowlisted module is optional in development/test.

    Import failures inside existing modules, invalid exports and unrecognized
    operations propagate instead of silently dropping functioning API modules.
    """
    loaded: list[LoadedRouter] = []
    missing: list[str] = []
    operations: set[str] = set()
    routes: set[tuple[str, str]] = set()
    for spec in ROUTER_SPECS:
        if not _enabled(spec, settings):
            continue
        name = f"benefitbridge.api.{spec.module}"
        try:
            module = import_module(name)
        except ModuleNotFoundError as error:
            if error.name != name:
                raise
            missing.append(spec.module)
            continue
        router = getattr(module, "router", None)
        if not isinstance(router, APIRouter):
            raise ConfigurationError(f"API module must export an APIRouter: {spec.module}")
        extra_handlers = getattr(module, "required_handlers", ())
        if not isinstance(extra_handlers, tuple) or not all(
            isinstance(key, str) and key for key in extra_handlers
        ):
            raise ConfigurationError(f"Invalid required_handlers declaration: {spec.module}")
        present: set[str] = set()
        for route in router.routes:
            if not isinstance(route, APIRoute) or route.operation_id not in spec.operations:
                raise ConfigurationError(f"Undocumented API operation in module: {spec.module}")
            if not route.include_in_schema:
                raise ConfigurationError("Application operations must be included in OpenAPI")
            operation = route.operation_id
            assert operation is not None
            if operation in operations:
                raise ConfigurationError(f"Duplicate API operation: {operation}")
            operations.add(operation)
            present.add(operation)
            if not route.path.startswith("/api/v1/"):
                raise ConfigurationError("Application routers must use the /api/v1 prefix")
            method, path = OPERATION_CONTRACTS[operation]
            if route.path != path or route.methods != {method}:
                raise ConfigurationError(f"API method/path differs from its contract: {operation}")
            for method in route.methods or ():
                key = (method, route.path)
                if key in routes:
                    raise ConfigurationError("Duplicate API method and path")
                routes.add(key)
        # Installed modules cannot declare readiness for endpoints they did not mount.
        if settings.app_env == "production" and present != set(spec.operations):
            raise ConfigurationError(f"Incomplete required P0/feature router: {spec.module}")
        loaded.append(
            LoadedRouter(spec, router, tuple(dict.fromkeys((*spec.handlers, *extra_handlers))))
        )
    if settings.app_env == "production" and missing:
        raise ConfigurationError("Missing required P0/feature routers: " + ", ".join(missing))
    return tuple(loaded)


def validate_handlers(
    loaded: tuple[LoadedRouter, ...], dependencies: Dependencies, settings: Settings
) -> None:
    required = {key for item in loaded for key in item.required_handlers}
    if settings.app_env == "production":
        required.update(kind.value for kind in RunKind if kind != RunKind.DEMO_RESET)
        if settings.demo_enabled:
            required.add(RunKind.DEMO_RESET.value)
    missing = sorted(required - dependencies.handlers.keys())
    if missing:
        raise ConfigurationError("Missing required stage handlers: " + ", ".join(missing))
    for kind in RunKind:
        binding = dependencies.handlers.get(kind.value)
        if kind.value in required and binding is not None and binding.scope != JobScope.PRIVATE:
            raise ConfigurationError("Private run entrypoints require private stage bindings")


def _install_feature_gate(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def gate(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        prefixes = ("/api/v1/watches", "/api/v1/notifications")
        if not settings.watch_enabled and any(
            path == prefix or path.startswith(prefix + "/") for prefix in prefixes
        ):
            supplied = request.headers.get("X-Request-ID", "")
            request_id = (
                supplied if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied) else str(uuid4())
            )
            problem = Problem(
                type="urn:benefitbridge:problem:feature-disabled",
                title="Feature disabled",
                status=403,
                detail="Saved-page watches are disabled.",
                code="FEATURE_DISABLED",
                request_id=request_id,
                errors=(),
                retryable=False,
            )
            return JSONResponse(
                problem.model_dump(mode="json"),
                status_code=403,
                media_type="application/problem+json",
                headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
            )
        return await call_next(request)


def register_routers(app: FastAPI, settings: Settings) -> None:
    """The single factory handoff from MS-001; validate before mounting anything."""
    if getattr(app.state, "registry_installed", False):
        raise ConfigurationError("API registry has already been installed")
    dependencies = getattr(app.state, "dependencies", None)
    if dependencies is None:
        dependencies = build_dependencies(settings)
    if not isinstance(dependencies, Dependencies):
        raise ConfigurationError("API registry requires typed Dependencies")
    loaded = load_routers(settings)
    validate_handlers(loaded, dependencies, settings)
    dependencies.validate(settings)
    app.state.settings = settings
    app.state.dependencies = dependencies
    # MS-002 uses Pydantic's validation schema as the single shared catalog.
    # Serialization mode drops default metadata on exclude_if fields, creating
    # conflicting definitions even for the same model (e.g. PredicateNode).
    app.separate_input_output_schemas = False
    app.openapi_schema = None
    for item in loaded:
        app.include_router(item.router)
    _install_feature_gate(app, settings)
    app.state.registry_installed = True
