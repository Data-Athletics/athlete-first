import typing
from typing import Literal, Optional

from sqlalchemy import Computed, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ModelBase

UserSex = Literal["male", "female"]

if typing.TYPE_CHECKING:
    from app.team.models import TeamMembership


class User(ModelBase):
    """Application user."""

    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_staff: Mapped[bool] = mapped_column(default=False)

    height: Mapped[float | None] = mapped_column(nullable=True)
    """Height in inches"""

    weight: Mapped[float | None] = mapped_column(nullable=True)
    """Weight in pounds"""

    sex: Mapped[UserSex | None] = mapped_column(nullable=True)
    """Either Male or Female"""

    age: Mapped[int | None] = mapped_column(nullable=True)
    """Age in years"""

    # Relationships
    memberships: Mapped[list["TeamMembership"]] = relationship(back_populates="user")

    # Computed fields
    can_login: Mapped[bool] = mapped_column(
        Computed(
            and_(hashed_password.is_not(None), is_active.is_(True)), persisted=True
        )
    )
