from pydantic import Field

from app.core.dtos import BaseDTO, BaseModelDTO


class BaseTeamDTO(BaseDTO):
    """Core fields used by all team DTOs"""

    name: str = Field(description="Team name")


class TeamDTO(BaseTeamDTO, BaseModelDTO):
    """Information for an existing team"""

    pass


class CreateTeamDTO(BaseTeamDTO):
    """Fields needed to create a team"""

    user_ids: list[int] = Field(
        default_factory=list, description="List of users to add to the team"
    )


class UpdateTeamDTO(BaseTeamDTO):
    """Fields on a team that can be updated"""

    name: str | None
