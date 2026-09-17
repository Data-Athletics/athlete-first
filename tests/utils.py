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
