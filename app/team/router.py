from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import CurrentUserDep, get_current_user
from app.core.dependencies import AsyncSessionDep
from app.team.dependencies import (
    CurrentUserTeamMembership,
    TeamByIdDep,
    TeamMembershipByIdDep,
)
from app.team.dtos.member_dsp_dto import MembershipDspDTO, SetMembershipDspDTO
from app.team.dtos.team_dsr_dto import SetTeamDsrDTO, TeamDsrDTO
from app.team.dtos.team_dto import CreateTeamDTO, MyTeamDTO, TeamDTO, UpdateTeamDTO
from app.team.dtos.team_membership_dto import (
    CreateTeamMembershipDTO,
    CreateTeamMembershipRequestDTO,
    TeamMemberDTO,
    TeamMembershipDTO,
    TeamMembershipRequestDTO,
    UpdateTeamMembershipDTO,
)
from app.team.models import MembershipDsp, TeamDsr
from app.team.services import (
    create_team,
    create_team_membership,
    create_team_membership_request,
    delete_team,
    delete_team_membership,
    get_effective_membership_dsp,
    get_effective_team_dsr,
    get_my_teams,
    get_team_by_id,
    list_non_approved_team_memberships,
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


@teams_router.get("/me", response_model=list[MyTeamDTO])
async def get_my_teams_route(db: AsyncSessionDep, user: CurrentUserDep):
    """Get the current user's teams and memberships"""

    return await get_my_teams(db, user)


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


@memberships_router.get("", response_model=list[TeamMemberDTO])
async def list_team_memberships_route(db: AsyncSessionDep, team: TeamByIdDep):
    """List team members for a specific team"""

    return await list_team_memberships(db, team)


@memberships_router.get("/non-approved", response_model=list[TeamMembershipRequestDTO])
async def list_non_approved_team_memberships_route(
    db: AsyncSessionDep, team: TeamByIdDep
):
    """List non-approved memberships for a team"""

    return await list_non_approved_team_memberships(db, team)


@memberships_router.post(
    "", response_model=TeamMembershipDTO, status_code=status.HTTP_201_CREATED
)
async def create_team_membership_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: CreateTeamMembershipDTO
):
    """Create a new membership for a team"""

    return await create_team_membership(db, team, body)


@memberships_router.post(
    "/request", response_model=TeamMembershipDTO, status_code=status.HTTP_201_CREATED
)
async def create_team_membership_request_route(
    db: AsyncSessionDep, team: TeamByIdDep, body: CreateTeamMembershipRequestDTO
):
    """Create a pending team membership request"""

    return await create_team_membership_request(db, team, body)


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


# ----------------------------------------
# Team data sharing requirements routes
# ----------------------------------------

team_dsr_router = APIRouter(
    prefix="/teams/{team_id}/data-sharing-requirements",
    dependencies=[Depends(get_team_by_id)],
)


@team_dsr_router.get("", response_model=TeamDsrDTO)
async def retrieve_team_dsr_route(team: TeamByIdDep):
    """Get the data sharing requirements for a team"""

    return get_effective_team_dsr(team)


@team_dsr_router.put("", response_model=TeamDsrDTO)
async def set_team_dsr_route(
    db: AsyncSessionDep, team: TeamByIdDep, user: CurrentUserDep, body: SetTeamDsrDTO
):
    """Fully update/replace a team's data sharing requirements"""

    payload = body.model_dump(exclude_unset=True)

    dsr: TeamDsr
    if team.dsr is not None:
        team.dsr.content = payload
        dsr = team.dsr
    else:
        dsr = TeamDsr(team_id=team.id, content=payload)

    db.add(dsr)
    await db.flush()
    await db.refresh(team)

    return get_effective_team_dsr(team)


router.include_router(team_dsr_router)

# ----------------------------------------
# Member data sharing policy routes
# ----------------------------------------

member_dsp_router = APIRouter(
    prefix="/teams/{team_id}/data-sharing-policy",
    dependencies=[Depends(get_team_by_id)],
)


@member_dsp_router.get("", response_model=MembershipDspDTO)
async def retrieve_membership_dsp_route(membership: CurrentUserTeamMembership):
    """Get the data sharing policy for the membership of the current user"""

    if membership.dsp is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="User has not accepted the data sharing policy yet",
        )

    return get_effective_membership_dsp(membership)


@member_dsp_router.put("", response_model=MembershipDspDTO)
async def set_membership_dsp_route(
    db: AsyncSessionDep,
    team: TeamByIdDep,
    membership: CurrentUserTeamMembership,
    body: SetMembershipDspDTO,
):
    """Fully update/replace the data sharing policy for the membership of the current user"""

    payload = body.model_dump(exclude_unset=True)

    # Check against default requirements
    dsr = get_effective_team_dsr(team)
    invalid_keys = []
    for key, value in payload.items():
        required_val = getattr(dsr, key, None)

        if required_val is None:
            continue

        if value != required_val:
            invalid_keys.append(key)

    if len(invalid_keys) != 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions based on team requirements: {','.join(invalid_keys)}",
        )

    # Set the new policy
    dsp: MembershipDsp
    if membership.dsp is not None:
        membership.dsp.content = payload
        dsp = membership.dsp
    else:
        dsp = MembershipDsp(membership_id=membership.id, content=payload)

    db.add(dsp)
    await db.flush()
    await db.refresh(membership)

    return get_effective_membership_dsp(membership)


router.include_router(member_dsp_router)


__all__ = ["router"]
