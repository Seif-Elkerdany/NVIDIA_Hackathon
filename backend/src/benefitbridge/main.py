"""Application factory and the sole handoff to M3's explicit API registry."""

from importlib import import_module
from typing import Protocol, cast

from fastapi import FastAPI

from benefitbridge.config import ConfigurationError, Settings, load_settings


class RegisterRouters(Protocol):
    """MS-003 binding: mount allowlisted routers and validate production composition.

    The registry exports register_routers(app, settings). It owns router order,
    optional development imports and required P0 router/handler checks (design §1).
    """

    def __call__(self, app: FastAPI, settings: Settings) -> None: ...


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()
    app = FastAPI(
        title="BenefitBridge",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    try:
        registry = import_module("benefitbridge.api.registry")
    except ModuleNotFoundError as error:
        # Only the unimplemented registry is optional; broken imports must propagate.
        if error.name not in {"benefitbridge.api", "benefitbridge.api.registry"}:
            raise
        if settings.app_env == "production":
            raise ConfigurationError("Production requires the MS-003 API registry") from None
    else:
        register = getattr(registry, "register_routers", None)
        if not callable(register):
            raise ConfigurationError("API registry must export register_routers(app, settings)")
        cast(RegisterRouters, register)(app, settings)
    return app
