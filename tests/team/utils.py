from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.team.models import (
    MembershipDsp,
    Team,
    TeamDsr,
    TeamMembership,
    TeamMembershipStatusType,
    TeamRoleType,
)
from app.user.models import User


@dataclass
class TeamMembershipsData:
    """Provides a few teams with varying levels of access for the current user"""

    t1: Team
    """Current user is coach"""

    t2: Team
    """Current user is athlete"""

    t3: Team
    """Current user is not a member"""

    t1_c1: TeamMembership
    """Current user"""
    t1_c2: TeamMembership
    t1_a1: TeamMembership

    t2_c1: TeamMembership
    t2_a1: TeamMembership
    """Current user"""
    t2_a2: TeamMembership

    t3_c1: TeamMembership
    t3_c2: TeamMembership
    t3_c3: TeamMembership
    t3_a1: TeamMembership

    def get_teams(self):
        return (self.t1, self.t2, self.t3)


async def create_test_team(
    db: AsyncSession | None = None,
    user_ids: list[int] | None = None,
    coach_user_ids: list[int] | None = None,
    users: list[User] | None = None,
    create_dsps: bool = False,
    create_dsr: bool = False,
    **kwargs,
):
    """Create mock team for testing"""

    if user_ids is not None or users is not None:
        assert db is not None, (
            "Must supply db connection if creating model relationships"
        )

    payload = {"name": fake.phrase(3), **kwargs}

    team = Team(**payload)

    if db:
        db.add(team)
        await db.flush()

        # Combine the `users` and `user_ids` list into one `user_ids` list without duplicates
        user_ids = list(set((user_ids or []) + [u.id for u in (users or [])]))
        mems = [
            TeamMembership(
                user_id=user_id,
                team_id=team.id,
                status=TeamMembershipStatusType.APPROVED,
            )
            for user_id in user_ids
        ]

        coaches = [
            TeamMembership(
                user_id=user_id,
                team_id=team.id,
                role=TeamRoleType.COACH,
                status=TeamMembershipStatusType.APPROVED,
            )
            for user_id in (coach_user_ids or [])
        ]

        db.add_all([*mems, *coaches])
        await db.flush()

        if create_dsps:
            mem_dsps = [MembershipDsp(membership_id=m.id) for m in mems]
            db.add_all(mem_dsps)

        if create_dsr:
            dsr = TeamDsr(team_id=team.id)
            db.add(dsr)

        await db.commit()
        await db.refresh(team)

    return team


async def create_test_teams(db: AsyncSession | None = None, count: int = 5, **kwargs):
    """Create multiple mock teams for testing"""

    teams = [await create_test_team(**kwargs) for _ in range(count)]

    # Save them all to the database at once
    if db:
        db.add_all(teams)
        await db.commit()
        for team in teams:
            await db.refresh(team)

    return teams


async def create_test_team_membership(
    db: AsyncSession,
    user_id: int,
    team_id: int,
    is_coach: bool = False,
    status=TeamMembershipStatusType.APPROVED,
    **kwargs,
):
    """Create a membership between a user and a team"""

    payload = {"user_id": user_id, "team_id": team_id, "status": status, **kwargs}

    if is_coach:
        payload["role"] = TeamRoleType.COACH

    membership = TeamMembership(**payload)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    return membership
