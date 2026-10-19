from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.core.dependencies import AsyncSessionDep
from app.team.dependencies import TeamByIdDep, TeamMembershipByIdDep
from app.team.dtos.team_dto import CreateTeamDTO, TeamDTO, UpdateTeamDTO
from app.team.dtos.team_membership_dto import (
    CreateTeamMembershipDTO,
    TeamMembershipDTO,
    UpdateTeamMembershipDTO,
)
from app.team.services import (
    create_team,
    create_team_membership,
    delete_team,
    delete_team_membership,
    get_team_by_id,
    list_team_memberships,
    list_teams,
    update_team,
    update_team_membership,
)

router = APIRouter(dependencies=[Depends(get_current_user)])

# -------------------------------
# Teams CRUD Routes
# -------------------------------

teams_router = APIRouter(prefix="/teams")


@teams_router.get("", response_model=list[TeamDTO])
async def list_teams_route(db: AsyncSessionDep):
    """Get a list of teams"""

    return await list_teams(db)


@teams_router.post("", response_model=TeamDTO, status_code=status.HTTP_201_CREATED)
async def create_team_route(db: AsyncSessionDep, body: CreateTeamDTO):
    """Create a new team"""

    return await create_team(db, body)


@teams_router.get("/{team_id}", response_model=TeamDTO)
async def retrieve_team_route(team: TeamByIdDep):
    """Retrieve a single team"""

    return team


@teams_router.patch("/{team_id}", response_model=TeamDTO)
async def update_team_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: UpdateTeamDTO
):
    """Partially update an existing team"""

    return await update_team(db, team, body)


@teams_router.delete("/{team_id}", response_model=TeamDTO)
async def delete_team_route(db: AsyncSessionDep, team: TeamByIdDep):
    """Delete an existing team and return the deleted team"""

    return await delete_team(db, team)


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

    return await list_team_memberships(db, team)


@memberships_router.post(
    "", response_model=TeamMembershipDTO, status_code=status.HTTP_201_CREATED
)
async def create_team_membership_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: CreateTeamMembershipDTO
):
    """Create a new membership for a team"""

    return await create_team_membership(db, team, body)


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

    return await update_team_membership(db, membership, body)


@memberships_router.delete("/{team_membership_id}", response_model=TeamMembershipDTO)
async def delete_team_membership_route(
    db: AsyncSessionDep, membership: TeamMembershipByIdDep
):
    """Remove a user from a team"""

    return await delete_team_membership(db, membership)


router.include_router(memberships_router)


__all__ = ["router"]
