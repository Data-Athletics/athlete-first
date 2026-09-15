from core.dependencies import AsyncSessionDep
from fastapi import APIRouter, HTTPException, status
from fastapi.logger import logger
from sqlalchemy import text

from app.observability.dtos import HealthDTO

router = APIRouter()


@router.get("/health")
async def get_health(db: AsyncSessionDep) -> HealthDTO:
    """Check core system functions and return 200 if healthy."""

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Received error from the database: {e}")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable"
        )
    return HealthDTO(status="healthy")
