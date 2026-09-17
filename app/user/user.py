from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import AsyncSessionDep

from .dtos.user_dto import UserDTO
from .models import User

users_router = APIRouter(prefix="/users")


@users_router.get("", response_model=list[UserDTO])
async def list_users(db: AsyncSessionDep):
    """Get a list of users from the database."""

    res = await db.execute(select(User))
    return res.scalars().all()


__all__ = ["users_router"]
