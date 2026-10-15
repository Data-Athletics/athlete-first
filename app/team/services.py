from typing import Annotated

from fastapi import Depends, Path

from app.core.dependencies import AsyncSessionDep
from app.team.models import Team


async def get_team_by_id(db: AsyncSessionDep, team_id: Annotated[int, Path()]) -> Team:
    """Retrieve team by their id or raise 404"""

    raise NotImplementedError()


async def get_team_membership_by_id(
    db: AsyncSessionDep,
    team: Annotated[Team, Depends(get_team_by_id)],
    team_membership_id: Annotated[int, Path()],
) -> Team:
    """Retrieve a team membership from a team or raise 404"""

    raise NotImplementedError()
