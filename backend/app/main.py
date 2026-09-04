import asyncio
import contextlib
import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.health import router as health_router
from app.api.routes.investigators import router as investigators_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.mock_bank import router as mock_bank_router
from app.api.errors import register_exception_handlers
from app.core.config import settings
from app.core.investigator_auth import require_investigator
from app.core.security import require_api_key

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def _lifespan(application: FastAPI):
    """Run the Mock Bank simulator alongside the app when enabled.

    Off by default under tests (see conftest) so a suite never writes simulated
    rows; the demo enables it through settings.
    """
    task = None
    if getattr(settings, "MOCK_BANK_SIMULATOR_ENABLED", False):
        from app.db.session import async_session_factory
        from app.services.alert_simulator import run_simulator_loop

        task = asyncio.create_task(
            run_simulator_loop(
                async_session_factory,
                min_interval=float(settings.MOCK_BANK_SIMULATOR_MIN_SECONDS),
                max_interval=float(settings.MOCK_BANK_SIMULATOR_MAX_SECONDS),
            )
        )
        logger.info(
            "alert-simulator: started (every %s-%ss)",
            settings.MOCK_BANK_SIMULATOR_MIN_SECONDS,
            settings.MOCK_BANK_SIMULATOR_MAX_SECONDS,
        )
    application.state.alert_simulator_task = task
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        # Local dev origins for the Next.js frontend (see README.md / DEPLOYMENT.md).
        # Wildcard origins are incompatible with allow_credentials=True.
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def _security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # Health stays open (deployment/uptime checks). Everything that reads or
    # acts on investigation/case/customer data requires the shared secret.
    application.include_router(health_router, prefix=settings.API_V1_PREFIX)
    application.include_router(
        investigations_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key), Depends(require_investigator)],
    )
    application.include_router(
        documents_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key), Depends(require_investigator)],
    )
    application.include_router(
        mock_bank_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key), Depends(require_investigator)],
    )
    application.include_router(
        alerts_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key), Depends(require_investigator)],
    )
    # API-key only at router level on purpose: /officers/lookup runs before
    # anyone is signed in. Every other route in this module declares
    # require_investigator itself, so nothing else is left open.
    application.include_router(
        investigators_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key)],
    )
    register_exception_handlers(application)

    return application


app: FastAPI = create_app()
