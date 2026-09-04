from fastapi import APIRouter

from app.services.gemini_client import _demo_mode_enabled

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str | bool]:
    """Health check endpoint to verify the service is running.

    Reports ``demo_mode`` as the *running process* resolves it. A change to
    .env or to the source only takes effect on restart, so an operator
    otherwise has no way to tell a stale server from a current one — which is
    exactly the confusion that makes a demo appear to ignore DEMO_MODE.
    """
    return {
        "status": "ok",
        "service": "ai-investigation-copilot",
        "demo_mode": _demo_mode_enabled(),
    }
