from app.core.dtos import BaseDTO, BaseModelDTO


class BaseTeamMembershipDTO(BaseDTO):
    """Core fields used by all team membership DTOs"""

    pass


class TeamMembershipDTO(BaseTeamMembershipDTO, BaseModelDTO):
    """Information for an existing team membership"""

    pass


class CreateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields needed to create a team membership"""

    pass


class UpdateTeamMembershipDTO(BaseTeamMembershipDTO):
    """Fields on a team membership that can be updated"""

    pass
