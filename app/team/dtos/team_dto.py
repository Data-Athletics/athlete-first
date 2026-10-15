from app.core.dtos import BaseDTO, BaseModelDTO


class BaseTeamDTO(BaseDTO):
    """Core fields used by all team DTOs"""

    pass


class TeamDTO(BaseTeamDTO, BaseModelDTO):
    """Information for an existing team"""

    pass


class CreateTeamDTO(BaseTeamDTO):
    """Fields needed to create a team"""

    pass


class UpdateTeamDTO(BaseTeamDTO):
    """Fields on a team that can be updated"""

    pass
