from sqlalchemy import ColumnExpressionArgument, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import ModelBase


async def model_count(
    db: AsyncSession,
    model: type[ModelBase],
    where: ColumnExpressionArgument[bool] | None = None,
) -> int:
    """Get the number of objects for a model in the database"""

    query = select(func.count(model.id)).select_from(model)

    if where is not None:
        query = query.where(where)

    res = await db.execute(query)
    return res.scalar_one()
