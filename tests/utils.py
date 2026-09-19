from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.user.models import User


async def create_test_user(db: Optional[AsyncSession] = None, **kwargs):
    """Create mock user for testing"""

    payload = {"username": fake.user_name(), **kwargs}
    user = User(**payload)

    if db:
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def create_test_users(db: Optional[AsyncSession] = None, count=5, **kwargs):
    """Create multiple test users"""

    users: list[User] = [await create_test_user(**kwargs) for _ in range(count)]

    # If there's a database, commit them all at once
    if db:
        db.add_all(users)
        await db.commit()

        for user in users:
            await db.refresh(user)

    return users
