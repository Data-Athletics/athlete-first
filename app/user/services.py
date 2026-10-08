from typing import Annotated

from fastapi import HTTPException, Path, status
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.services import get_password_hash
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


async def create_user(
    db: AsyncSessionDep, username: str, password: SecretStr | str | None, **kwargs
) -> User:
    """Create a new user and set their password"""

    # Extract and hash password
    if isinstance(password, SecretStr):
        password = password.get_secret_value()

    if password is not None:
        kwargs["hashed_password"] = get_password_hash(password)

    # Set user fields
    user = User(username=username, **kwargs)
    db.add(user)

    # Try to save changes, raise 400 if there's a unique violation
    try:
        await db.flush()
        await db.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        ) from e

    return user
