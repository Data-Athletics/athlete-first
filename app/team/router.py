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
from app.team.services import get_team_by_id

router = APIRouter(dependencies=[Depends(get_current_user)])

# -------------------------------
# Teams CRUD Routes
# -------------------------------

teams_router = APIRouter(prefix="/teams")


@teams_router.get("", response_model=list[TeamDTO])
async def list_teams_route(db: AsyncSessionDep):
    """Get a list of teams"""

    raise NotImplementedError()


@teams_router.post("", response_model=TeamDTO, status_code=status.HTTP_201_CREATED)
async def create_team_route(db: AsyncSessionDep, body: CreateTeamDTO):
    """Create a new team"""

    raise NotImplementedError()


@teams_router.get("/{team_id}", response_model=TeamDTO)
async def retrieve_team_route(db: AsyncSessionDep, team: TeamByIdDep):
    """Retrieve a single team"""

    raise NotImplementedError()


@teams_router.patch("/{team_id}", response_model=TeamDTO)
async def update_team_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: UpdateTeamDTO
):
    """Partially update an existing team"""

    raise NotImplementedError()


@teams_router.delete("/{team_id}", response_model=TeamDTO)
async def delete_team_route(db: AsyncSessionDep, team: TeamByIdDep):
    """Delete an existing team and return the deleted team"""

    raise NotImplementedError()


router.include_router(teams_router)


# -------------------------------
# Team Members CRUD Routes
# -------------------------------

memberships_router = APIRouter(
    prefix="/teams/{team_id}/memberships", dependencies=[Depends(get_team_by_id)]
)


@memberships_router.get("", response_model=list[TeamMembershipDTO])
async def list_team_memberships_route(db: AsyncSessionDep):
    """List team members for a specific team"""

    raise NotImplementedError()


@memberships_router.post("", response_model=TeamMembershipDTO)
async def create_team_membership_route(
    db: AsyncSessionDep, body: CreateTeamMembershipDTO
):
    """Create a new membership for a team"""

    raise NotImplementedError()


@memberships_router.get("/{team_membership_id}", response_model=TeamMembershipDTO)
async def retrieve_team_membership_route(
    db: AsyncSessionDep, membership: TeamMembershipByIdDep
):
    """Retrieve a single team membership from a team"""

    raise NotImplementedError()


@memberships_router.patch("/{team_membership_id}", response_model=TeamMembershipDTO)
async def update_team_membership_route(
    db: AsyncSessionDep,
    membership: TeamMembershipByIdDep,
    body: UpdateTeamMembershipDTO,
):
    """Partially update a single team membership"""

    raise NotImplementedError()


@memberships_router.delete("/{team_membership_id}", response_model=TeamMembershipDTO)
async def delete_team_membership_route(
    db: AsyncSessionDep, membership: TeamMembershipByIdDep
):
    """Remove a user from a team"""

    raise NotImplementedError()


router.include_router(memberships_router)


__all__ = ["router"]
