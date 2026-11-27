from pydantic import Field

from app.core.dtos import BaseDTO, BaseModelDTO
from app.team.dtos.team_membership_dto import TeamMembershipDTO
from app.team.models import Team, TeamMembership
from app.user.models import User


class BaseTeamDTO(BaseDTO):
    """Core fields used by all team DTOs"""

    name: str = Field(description="Team name")


class TeamDTO(BaseTeamDTO, BaseModelDTO):
    """Information for an existing team"""

    pass


class MyTeamDTO(TeamDTO):
    """A team and the current user's membership in that team"""

    membership: TeamMembershipDTO | None = Field(default=None)

    @classmethod
    def from_models(cls, team: Team, membership: TeamMembership | None):
        """Extract the DTO from a team and a membership model"""

        return cls.model_validate(
            {**TeamDTO.model_validate(team).model_dump(), "membership": membership}
        )

    @classmethod
    def from_team(cls, team: Team, principal: User):
        """Auto populate the membership field with the membership of the principal"""

        membership = next(
            (mem for mem in team.memberships if mem.user_id == principal.id), None
        )
        return cls.from_models(team, membership)


class CreateTeamDTO(BaseTeamDTO):
    """Fields needed to create a team"""

    user_ids: list[int] = Field(
        default_factory=list, description="List of users to add to the team"
    )


class UpdateTeamDTO(BaseTeamDTO):
    """Fields on a team that can be updated"""

    name: str | None
