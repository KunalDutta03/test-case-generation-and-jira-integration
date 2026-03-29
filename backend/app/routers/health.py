from fastapi import APIRouter
from app.schemas import HealthResponse
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.app_environment,
    )
