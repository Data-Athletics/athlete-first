from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import and_, select

from app.core.dependencies import AsyncSessionDep
from app.team.models import Team, TeamMembership


async def get_team_by_id(db: AsyncSessionDep, team_id: Annotated[int, Path()]) -> Team:
    """Retrieve team by their id or raise 404"""

    rows = await db.execute(select(Team).where(Team.id == team_id))
    team = rows.scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Team not found for id {team_id}"
        )

    return team


async def get_team_membership_by_id(
    db: AsyncSessionDep,
    team: Annotated[Team, Depends(get_team_by_id)],
    team_membership_id: Annotated[int, Path()],
) -> TeamMembership:
    """Retrieve a team membership from a team or raise 404"""

    rows = await db.execute(
        select(TeamMembership).where(
            and_(
                TeamMembership.id == team_membership_id,
                TeamMembership.team_id == team.id,
            )
        )
    )
    membership = rows.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Team membership not found for id {team_membership_id} in team {team.name}",
        )

    return membership
