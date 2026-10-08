from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import ModelBase


async def model_count(db: AsyncSession, model: type[ModelBase]) -> int:
    """Get the number of objects for a model in the database"""

    res = await db.execute(select(func.count(model.id)).select_from(model))
    return res.scalar_one()
