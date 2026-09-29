from typing import Literal, Optional

from sqlalchemy import Computed, and_
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ModelBase

UserSex = Literal["Male", "Female"]


class User(ModelBase):
    """Application user."""

    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)

    height: Mapped[float] = mapped_column()
    """Height in inches"""

    weight: Mapped[float] = mapped_column()
    """Weight in pounds"""

    sex: Mapped[UserSex] = mapped_column()
    """Either Male or Female"""

    age: Mapped[int] = mapped_column()
    """Age in years"""

    # Computed fields
    can_login: Mapped[bool] = mapped_column(
        Computed(
            and_(hashed_password.is_not(None), is_active.is_(True)), persisted=True
        )
    )
