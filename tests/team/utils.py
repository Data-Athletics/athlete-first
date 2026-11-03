from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.team.models import Team, TeamMembership, TeamMembershipStatusType
from app.user.models import User


async def create_test_team(
    db: AsyncSession | None = None,
    user_ids: list[int] | None = None,
    users: list[User] | None = None,
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
                status=TeamMembershipStatusType.APPROVE,
            )
            for user_id in user_ids
        ]
        db.add_all(mems)

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
