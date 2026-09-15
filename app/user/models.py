from typing import Optional

from sqlalchemy import Computed, and_
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ModelBase


class User(ModelBase):
    """Application user."""

    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Computed fields
    can_login: Mapped[bool] = mapped_column(
        Computed(
            and_(hashed_password.is_not(None), is_active.is_(True)), persisted=True
        )
    )
