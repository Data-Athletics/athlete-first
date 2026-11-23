from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import CurrentUserDep
from app.core.dependencies import AsyncSessionDep
from app.team.dtos.team_membership_dto import TeamAccessLevel
from app.team.models import Team, TeamMembership, TeamRoleType
from app.team.services import (
    get_team_by_id,
    get_team_membership_by_id,
    get_user_team_membership,
    require_team_coach,
)

TeamByIdDep = Annotated[Team, Depends(get_team_by_id)]
"""
Retreive a single team by it's id in the url path,
or raise a 404 error if it's not found.
"""

CurrentUserTeamMembership = Annotated[TeamMembership, Depends(get_user_team_membership)]
"""
For a route with `team_id`, fetch the team membership
for the current authenticated user, or return 404 if the user
is not a member of the team.
"""

TeamMembershipByIdDep = Annotated[TeamMembership, Depends(get_team_membership_by_id)]
"""
Retreive a single team membership by it's id in the url path
and by the team id in the url path, or raise a 404 if it's not found.
"""


async def current_user_is_any_coach_dep(db: AsyncSessionDep, user: CurrentUserDep):
    """Dependency to check if the user is a coach of any team"""

    await require_team_coach(db, user=user)


async def current_user_is_team_coach_dep(
    db: AsyncSessionDep, user: CurrentUserDep, team: TeamByIdDep
):
    """Dependency to check if current user is a coach for the specific team"""

    await require_team_coach(db, user=user, team=team)


async def current_user_team_access_dep(
    db: AsyncSessionDep, user: CurrentUserDep, team: TeamByIdDep
) -> TeamAccessLevel:
    """Get the level of access a user has within a team"""

    if user.is_effective_staff:
        return TeamAccessLevel.STAFF

    membership = next((mem for mem in team.memberships if mem.user_id == user.id), None)

    if membership is None:
        return TeamAccessLevel.NONE
    elif membership.role == TeamRoleType.COACH:
        return TeamAccessLevel.COACH
    else:
        return TeamAccessLevel.ATHLETE


CurrentUserTeamAccessDep = Annotated[
    TeamAccessLevel, Depends(current_user_team_access_dep)
]
"""
Get the level of access the current user has within a team
retrieved by id from the url `team_id` parameter.
"""
