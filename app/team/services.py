from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import and_, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import DBErrors
from app.core.dependencies import AsyncSessionDep
from app.team.dtos.team_dto import CreateTeamDTO, MyTeamDTO, UpdateTeamDTO
from app.team.dtos.team_membership_dto import (
    CreateTeamMembershipDTO,
    CreateTeamMembershipRequestDTO,
    TeamMembershipRequestDTO,
    UpdateTeamMembershipDTO,
)
from app.team.models import Team, TeamMembership, TeamMembershipStatusType
from app.user.models import User

# -------------------------------
# Teams CRUD
# -------------------------------


async def list_teams(db: AsyncSession) -> list[Team]:
    """Get a list of all teams"""

    rows = await db.execute(select(Team).order_by(desc(Team.id)))
    return list(rows.scalars())


async def get_my_teams(db: AsyncSession, user: User) -> list[MyTeamDTO]:
    """Get all teams and memberships for the current user."""

    rows = await db.execute(
        select(Team, TeamMembership)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .where(TeamMembership.user_id == user.id)
        .order_by(desc(Team.id))
    )

    return [
        MyTeamDTO.model_validate(
            {
                "id": team.id,
                "created_at": team.created_at,
                "updated_at": team.updated_at,
                "name": team.name,
                "membership": membership,
            }
        )
        for team, membership in rows.all()
    ]


async def get_team_by_id(db: AsyncSessionDep, team_id: Annotated[int, Path()]) -> Team:
    """Retrieve team by their id or raise 404"""

    rows = await db.execute(select(Team).where(Team.id == team_id))
    team = rows.scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Team not found for id {team_id}"
        )

    return team


async def create_team(db: AsyncSession, body: CreateTeamDTO):
    """Create new team"""

    payload = body.model_dump()
    user_ids = payload.pop("user_ids", [])

    # Create the team
    team = Team(**payload)
    db.add(team)

    try:
        await db.flush()
        await db.refresh(team)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Team already exists"
        ) from e

    # Add users to the team
    for id in user_ids:
        mem = TeamMembership(
            user_id=id, team_id=team.id, status=TeamMembershipStatusType.APPROVE
        )
        db.add(mem)

    if user_ids:
        await db.flush()

    return team


async def update_team(db: AsyncSession, team: Team, body: UpdateTeamDTO):
    """Update a team"""

    data = body.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(team, key, value)

    db.add(team)

    try:
        await db.flush()
        await db.refresh(team)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team already exists with the new values",
        ) from e

    return team


async def delete_team(db: AsyncSession, team: Team):
    """Delete a team from the database"""

    await db.delete(team)
    await db.flush()

    return team


# -------------------------------
# Team Members CRUD
# -------------------------------


async def list_team_memberships(db: AsyncSession, team: Team) -> list[TeamMembership]:
    """List team memberships for a team"""

    rows = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_id == team.id)
        .order_by(desc(TeamMembership.id))
    )
    return list(rows.scalars())


async def list_non_approved_team_memberships(
    db: AsyncSession, team: Team
) -> list[TeamMembershipRequestDTO]:
    """List all non-approved memberships for a team."""

    rows = await db.execute(
        select(TeamMembership, User.username)
        .join(User, User.id == TeamMembership.user_id)
        .where(
            TeamMembership.team_id == team.id,
            TeamMembership.status != TeamMembershipStatusType.APPROVE,
        )
        .order_by(desc(TeamMembership.id))
    )

    return [
        TeamMembershipRequestDTO.model_validate(
            {
                "id": membership.id,
                "created_at": membership.created_at,
                "updated_at": membership.updated_at,
                "role": membership.role,
                "user_id": membership.user_id,
                "team_id": membership.team_id,
                "status": membership.status,
                "username": username,
                "team_name": team.name,
            }
        )
        for membership, username in rows.all()
    ]


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


async def _create_team_membership(
    db: AsyncSession,
    team: Team,
    user_id: int,
    membership_status: TeamMembershipStatusType,
):
    """Create a team membership with an explicit status"""

    membership = TeamMembership(
        user_id=user_id, team_id=team.id, status=membership_status
    )
    db.add(membership)

    try:
        await db.flush()
        await db.refresh(membership)
    except IntegrityError as e:
        # Get underlying db error
        pgcode = getattr(e.orig, "pgcode", None)

        # Return proper exception based on the actual error
        if pgcode == DBErrors.UNIQUE_VIOLATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team membership already exists",
            ) from e
        elif pgcode == DBErrors.FOREIGN_KEY_VIOLATION:
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "user_id"],
                        "msg": f"No user exists with id {user_id}",
                        "type": "value_error",
                    }
                ]
            ) from e

        raise e

    return membership


async def create_team_membership(
    db: AsyncSession, team: Team, body: CreateTeamMembershipDTO
):
    """Create an approved team membership"""

    return await _create_team_membership(
        db, team, body.user_id, TeamMembershipStatusType.APPROVE
    )


async def create_team_membership_request(
    db: AsyncSession, team: Team, body: CreateTeamMembershipRequestDTO
):
    """Create a pending team membership request"""

    rows = await db.execute(select(User).where(User.username == body.username))
    user = rows.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"User not found for username {body.username}",
        )

    return await _create_team_membership(
        db, team, user.id, TeamMembershipStatusType.PENDING
    )


async def update_team_membership(
    db: AsyncSession, membership: TeamMembership, body: UpdateTeamMembershipDTO
):
    """Update a team membership"""

    data = body.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(membership, key, value)

    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    return membership


async def delete_team_membership(db: AsyncSession, membership: TeamMembership):
    """Remove a user from a team"""

    await db.delete(membership)
    await db.flush()

    return membership
