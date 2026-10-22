from pydantic import Field

from app.core.dtos import BaseDTO, BaseModelDTO
from app.team.models import TeamMembershipStatusType, TeamRoleType


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


class TeamMembershipRequestDTO(TeamMembershipDTO):
    """A membership request with the user and team display names"""

    username: str
    team_name: str


class CreateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields needed to create a team membership"""

    user_id: int


class CreateTeamMembershipRequestDTO(BaseTeamMembershipDTO):
    """Fields needed to request a team membership"""

    username: str


class UpdateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields on a team membership that can be updated"""

    role: TeamRoleType | None = Field(default=None)
    status: TeamMembershipStatusType | None = Field(default=None)
