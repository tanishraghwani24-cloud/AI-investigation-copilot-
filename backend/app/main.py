from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.mock_bank import router as mock_bank_router
from app.api.errors import register_exception_handlers
from app.core.config import settings
from app.core.security import require_api_key


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
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
        dependencies=[Depends(require_api_key)],
    )
    application.include_router(
        documents_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key)],
    )
    application.include_router(
        mock_bank_router,
        prefix=settings.API_V1_PREFIX,
        dependencies=[Depends(require_api_key)],
    )
    register_exception_handlers(application)

    return application


app: FastAPI = create_app()
