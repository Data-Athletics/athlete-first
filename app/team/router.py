from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import get_current_user
from app.core.database import DBErrors
from app.core.dependencies import AsyncSessionDep
from app.team.dependencies import TeamByIdDep, TeamMembershipByIdDep
from app.team.dtos.team_dto import CreateTeamDTO, TeamDTO, UpdateTeamDTO
from app.team.dtos.team_membership_dto import (
    CreateTeamMembershipDTO,
    TeamMembershipDTO,
    UpdateTeamMembershipDTO,
)
from app.team.models import Team, TeamMembership
from app.team.services import get_team_by_id

router = APIRouter(dependencies=[Depends(get_current_user)])

# -------------------------------
# Teams CRUD Routes
# -------------------------------

teams_router = APIRouter(prefix="/teams")


@teams_router.get("", response_model=list[TeamDTO])
async def list_teams_route(db: AsyncSessionDep):
    """Get a list of teams"""

    rows = await db.execute(select(Team).order_by(desc(Team.id)))
    return rows.scalars()


@teams_router.post("", response_model=TeamDTO, status_code=status.HTTP_201_CREATED)
async def create_team_route(db: AsyncSessionDep, body: CreateTeamDTO):
    """Create a new team"""

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
        mem = TeamMembership(user_id=id, team_id=team.id)
        db.add(mem)

    if user_ids:
        await db.flush()

    return team


@teams_router.get("/{team_id}", response_model=TeamDTO)
async def retrieve_team_route(team: TeamByIdDep):
    """Retrieve a single team"""

    return team


@teams_router.patch("/{team_id}", response_model=TeamDTO)
async def update_team_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: UpdateTeamDTO
):
    """Partially update an existing team"""

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


@teams_router.delete("/{team_id}", response_model=TeamDTO)
async def delete_team_route(db: AsyncSessionDep, team: TeamByIdDep):
    """Delete an existing team and return the deleted team"""

    await db.delete(team)
    await db.flush()

    return team


router.include_router(teams_router)


# -------------------------------
# Team Members CRUD Routes
# -------------------------------

memberships_router = APIRouter(
    prefix="/teams/{team_id}/memberships", dependencies=[Depends(get_team_by_id)]
)


@memberships_router.get("", response_model=list[TeamMembershipDTO])
async def list_team_memberships_route(db: AsyncSessionDep, team: TeamByIdDep):
    """List team members for a specific team"""

    rows = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_id == team.id)
        .order_by(desc(TeamMembership.id))
    )
    return rows.scalars()


@memberships_router.post(
    "", response_model=TeamMembershipDTO, status_code=status.HTTP_201_CREATED
)
async def create_team_membership_route(
    db: AsyncSessionDep, body: CreateTeamMembershipDTO, team: TeamByIdDep
):
    """Create a new membership for a team"""

    membership = TeamMembership(**body.model_dump(), team_id=team.id)
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
                        "msg": f"No user exists with id {body.user_id}",
                        "type": "value_error",
                    }
                ]
            ) from e

        raise e

    return membership


@memberships_router.get("/{team_membership_id}", response_model=TeamMembershipDTO)
async def retrieve_team_membership_route(membership: TeamMembershipByIdDep):
    """Retrieve a single team membership from a team"""

    return membership


@memberships_router.patch("/{team_membership_id}", response_model=TeamMembershipDTO)
async def update_team_membership_route(
    db: AsyncSessionDep,
    membership: TeamMembershipByIdDep,
    body: UpdateTeamMembershipDTO,
):
    """Partially update a single team membership"""

    data = body.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(membership, key, value)

    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    return membership


@memberships_router.delete("/{team_membership_id}", response_model=TeamMembershipDTO)
async def delete_team_membership_route(
    db: AsyncSessionDep, membership: TeamMembershipByIdDep
):
    """Remove a user from a team"""

    await db.delete(membership)
    await db.flush()

    return membership


router.include_router(memberships_router)


__all__ = ["router"]
