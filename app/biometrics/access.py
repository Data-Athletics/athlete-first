from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUserDep
from app.core.dependencies import AsyncSessionDep
from app.team.models import TeamMembership, TeamMembershipStatusType, TeamRoleType
from app.team.services import get_effective_membership_dsp
from app.user.dependencies import UserByIdDep
from app.user.models import User

MetricSharingField = Literal[
    "bpm_shared",
    "rhr_shared",
    "calories_shared",
    "respiratory_rate_shared",
    "hrv_shared",
    "effort_shared",
    "skin_temp_delta_shared",
]


def require_metric_access(field: MetricSharingField):
    """Build a reusable FastAPI dependency for one shared metric field."""

    async def metric_access_dependency(
        db: AsyncSessionDep, current_user: CurrentUserDep, target_user: UserByIdDep
    ) -> None:
        await enforce_metric_access(db, current_user, target_user, field)

    return metric_access_dependency


async def enforce_metric_access(
    db: AsyncSession, current_user: User, target_user: User, field: MetricSharingField
) -> None:
    """Allow an owner or an approved coach to read a shared metric."""

    if current_user.is_admin:
        return

    coach_team_ids = await _approved_team_ids_for_user(
        db, current_user.id, None if current_user.is_staff else TeamRoleType.COACH
    )

    if current_user.id == target_user.id:
        memberships = await _get_approved_memberships(
            db, target_user.id, TeamRoleType.ATHLETE
        )
        if any(
            membership.dsp is None
            or get_effective_membership_dsp(membership).invalid_fields
            for membership in memberships
        ):
            raise _sharing_denied()
        return

    if not coach_team_ids:
        raise _sharing_denied()

    memberships = await _get_approved_memberships(
        db, target_user.id, TeamRoleType.ATHLETE, coach_team_ids
    )
    for membership in memberships:
        if membership.dsp is None:
            continue

        policy = get_effective_membership_dsp(membership)
        if policy.invalid_fields:
            continue
        if getattr(policy, field, False) is True:
            return

    raise _sharing_denied()


async def _approved_team_ids_for_user(
    db: AsyncSession, user_id: int, role: TeamRoleType | None
) -> set[int]:
    statement = select(TeamMembership.team_id).where(
        TeamMembership.user_id == user_id,
        TeamMembership.status == TeamMembershipStatusType.APPROVE,
    )
    if role is not None:
        statement = statement.where(TeamMembership.role == role)

    result = await db.execute(statement)
    return set(result.scalars())


async def _get_approved_memberships(
    db: AsyncSession, user_id: int, role: TeamRoleType, team_ids: set[int] | None = None
) -> list[TeamMembership]:
    statement = select(TeamMembership).where(
        TeamMembership.user_id == user_id,
        TeamMembership.role == role,
        TeamMembership.status == TeamMembershipStatusType.APPROVE,
    )
    if team_ids is not None:
        statement = statement.where(TeamMembership.team_id.in_(team_ids))

    result = await db.execute(statement)
    return list(result.scalars())


def _sharing_denied() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This metric is not available under the current data sharing policy.",
    )
