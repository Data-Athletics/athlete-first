from enum import StrEnum

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ModelBase, ValuesEnum
from app.user.models import User


class TeamRoleType(StrEnum):
    """The different relationship types a user can have with a team"""

    COACH = "coach"
    ATHLETE = "athlete"


class TeamMembershipStatusType(StrEnum):
    """The different consent statuses a user can have for a team membership"""

    APPROVE = "approve"
    REJECT = "reject"
    PENDING = "pending"


class Team(ModelBase):
    """Represents an athletic team with coaches and athletes"""

    name: Mapped[str] = mapped_column(unique=True)

    # Relationships
    memberships: Mapped[list["TeamMembership"]] = relationship(
        back_populates="team",
        lazy="selectin",
        order_by="desc(TeamMembership.id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TeamMembership(ModelBase):
    """A user's relationship with a team"""

    role: Mapped[TeamRoleType] = mapped_column(
        ValuesEnum(TeamRoleType), default=TeamRoleType.ATHLETE
    )
    status: Mapped[TeamMembershipStatusType] = mapped_column(
        ValuesEnum(TeamMembershipStatusType), default=TeamMembershipStatusType.PENDING
    )

    # Relationships
    team_id: Mapped[int] = mapped_column(ForeignKey(Team.id, ondelete="CASCADE"))
    team: Mapped[Team] = relationship(
        back_populates="memberships", foreign_keys=[team_id], lazy="joined"
    )

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    user: Mapped[User] = relationship(
        back_populates="memberships", foreign_keys=[user_id], lazy="joined"
    )

    __table_args__ = (UniqueConstraint(team_id, user_id, name="uq_team_user"),)
