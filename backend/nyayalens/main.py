"""FastAPI application entry point.

App factory pattern (`create_app`) so tests can construct isolated instances.
Route modules register themselves through explicit `include_router` calls —
no implicit discovery.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nyayalens import __version__
from nyayalens.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks.

    Kept intentionally small: initialise adapter singletons here once code
    for them lands. The tests rely on being able to construct `create_app`
    without side effects, so nothing in the lifespan must talk to the
    network by default.
    """
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured FastAPI instance.

    Args:
        settings: injection point for tests; defaults to `get_settings()`.
    """
    cfg = settings or get_settings()

    app = FastAPI(
        title="NyayaLens API",
        description="AI accountability operating system for hiring fairness.",
        version=__version__,
        docs_url="/docs" if not cfg.is_production else None,
        redoc_url="/redoc" if not cfg.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        """Liveness probe for Cloud Run and local smoke tests."""
        return {
            "status": "ok",
            "version": __version__,
            "env": cfg.nyayalens_env,
            "emulators": "on" if cfg.is_using_emulators else "off",
        }

    # Route modules will be included here as they land in Week 1-2:
    # from nyayalens.api import datasets, audits, probes, recourse, reports
    # app.include_router(datasets.router, prefix="/api/v1")
    # app.include_router(audits.router,   prefix="/api/v1")
    # ...

    return app


# Module-level instance so `uvicorn nyayalens.main:app` works.
app = create_app()
