from typing import Annotated

from fastapi import Depends

from app.team.models import Team, TeamMembership
from app.team.services import (
    get_team_by_id,
    get_team_membership_by_id,
    get_user_team_membership,
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
