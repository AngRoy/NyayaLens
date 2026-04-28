"""FastAPI application entry point.

App factory pattern (`create_app`) so tests can construct isolated instances.
Route modules register themselves through explicit `include_router` calls —
no implicit discovery.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nyayalens import __version__
from nyayalens.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks.

    Adapter singletons (`AppState`, `AuditSink`, `LLMClient`, ...) are
    constructed lazily on first request inside
    `nyayalens.api.deps._ensure_singletons`, so the lifespan body stays a
    no-op. Tests rely on being able to construct `create_app` without
    network side effects; nothing here must talk to the network.
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
        allow_origin_regex=cfg.cors_origin_regex,
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

    from nyayalens.api.routes import router as api_router

    app.include_router(api_router, prefix="/api/v1")

    return app


# Module-level instance so `uvicorn nyayalens.main:app` works.
app = create_app()
