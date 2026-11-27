from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from app.core.dtos import BaseDTO, BaseModelDTO
from app.team.models import TeamMembership, TeamMembershipStatusType, TeamRoleType


class TeamAccessLevel(StrEnum):
    """The kind of permissions a user has within a team"""

    STAFF = "staff"
    """The user is marked as either staff or admin"""
    COACH = "coach"
    """The user has a membership with the role coach for the team"""
    ATHLETE = "athlete"
    """The user has a membership with the role athlete for the team"""
    NONE = "none"
    """The user is not a member of the team"""


class BaseTeamMembershipDTO(BaseDTO):
    """Core fields used by all team membership DTOs"""

    role: TeamRoleType = Field(
        description="Determines what kind of data the user can see",
        default=TeamRoleType.ATHLETE,
    )


class TeamMembershipDTO(BaseTeamMembershipDTO, BaseModelDTO):
    """Information for an existing team membership"""

    user_id: int = Field(description="User associated with the membership")
    team_id: int = Field(description="Team associated with the membership")
    status: TeamMembershipStatusType = Field(description="Status of membership consent")


class TeamMemberDTO(TeamMembershipDTO):
    """A team membership with the user's display name"""

    name: str
    team_name: str

    @classmethod
    def from_team_membership(cls, team_membership: TeamMembership):
        """Extract DTO from a team membership object"""

        return cls.model_validate(
            {
                **TeamMembershipDTO.model_validate(team_membership).model_dump(),
                "name": team_membership.user.name,
                "team_name": team_membership.team.name,
            }
        )


class CreateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields needed to create a team membership"""

    user_id: int | None = Field(default=None)
    username: str | None = Field(default=None)

    @model_validator(mode="after")
    def check_user_fields(self) -> Self:
        if self.user_id is None and self.username is None:
            raise ValueError("Must set `user_id` or `username`")
        return self


class UpdateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields on a team membership that can be updated"""

    role: TeamRoleType | None = Field(default=None)
    status: TeamMembershipStatusType | None = Field(default=None)
