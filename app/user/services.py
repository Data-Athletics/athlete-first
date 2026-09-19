from typing import Annotated

from fastapi import HTTPException, Path, status
from sqlalchemy import select

from app.core.dependencies import AsyncSessionDep
from app.user.models import User


async def get_user_by_id(db: AsyncSessionDep, user_id: Annotated[int, Path()]) -> User:
    """Retrieve user by ID or raise 404"""

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User not found for id {user_id}"
        )

    return user
