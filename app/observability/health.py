from fastapi import APIRouter

from app.observability.dtos import HealthDTO

router = APIRouter()


@router.get("/health")
async def get_health() -> HealthDTO:
    return HealthDTO(status="healthy")
