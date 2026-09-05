from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.api.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
