from pydantic import Field

from app.core.dtos import BaseDTO


class BaseTeamDsrDTO(BaseDTO):
    """Fields a coach can set for the team's data sharing requirements"""

    bpm_shared: bool | None = Field(default=None)
    calories_shared: bool | None = Field(default=None)
    respiratory_rate_shared: bool | None = Field(default=None)
    hrv_shared: bool | None = Field(default=None)
    effort_shared: bool | None = Field(default=None)
    skin_temp_delta_shared: bool | None = Field(default=None)


class SetTeamDsrDTO(BaseTeamDsrDTO):
    """Minimum data sharing requirements for all athletes in a team"""

    pass


class TeamDsrDTO(BaseTeamDsrDTO):
    """Minimum data sharing requirements for all athletes in a team"""

    team_id: int = Field(description="Associated team")
