import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.models import Team
from app.user.models import User
from tests.team.utils import TeamMembershipsData, create_test_team
from tests.user.utils import create_test_users


@pytest.fixture(scope="function", name="team_memberships_data")
async def setup_team_memberships_data(db: AsyncSession, current_user: User):
    """Create team membership data for the current user"""

    t1_c2, t1_a1, t2_c1, t2_a2, t3_c1, t3_c2, t3_c3, t3_a1 = await create_test_users(
        db, count=8
    )

    t1 = await create_test_team(
        db,
        coach_user_ids=[current_user.id, t1_c2.id],
        user_ids=[t1_a1.id],
        create_dsr=True,
    )
    t2 = await create_test_team(
        db,
        coach_user_ids=[t2_c1.id],
        user_ids=[current_user.id, t2_a2.id],
        create_dsr=True,
    )
    t3 = await create_test_team(
        db,
        coach_user_ids=[t3_c1.id, t3_c2.id, t3_c3.id],
        user_ids=[t3_a1.id],
        create_dsr=True,
    )

    def _get_membership(t: Team, u: User):
        return next(m for m in t.memberships if m.user_id == u.id)

    return TeamMembershipsData(
        t1=t1,
        t2=t2,
        t3=t3,
        t1_c1=_get_membership(t1, current_user),
        t1_c2=_get_membership(t1, t1_c2),
        t1_a1=_get_membership(t1, t1_a1),
        t2_c1=_get_membership(t2, t2_c1),
        t2_a1=_get_membership(t2, current_user),
        t2_a2=_get_membership(t2, t2_a2),
        t3_c1=_get_membership(t3, t3_c1),
        t3_c2=_get_membership(t3, t3_c2),
        t3_c3=_get_membership(t3, t3_c3),
        t3_a1=_get_membership(t3, t3_a1),
    )
