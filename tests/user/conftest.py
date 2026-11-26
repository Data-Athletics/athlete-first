import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.team.utils import create_test_team
from tests.user.utils import UserPermsData, create_test_user, create_test_users


@pytest.fixture(scope="function", name="user_perms_data")
async def setup_user_perms_data(db: AsyncSession):
    """Create users in various roles provided by the system"""

    u1, tc1, ta1 = await create_test_users(db, count=3)
    s1 = await create_test_user(db, is_staff=True)
    a1 = await create_test_user(db, is_admin=True)

    team = await create_test_team(db, coach_user_ids=[tc1.id], user_ids=[ta1.id])

    return UserPermsData(u1=u1, s1=s1, a1=a1, t1=team, tc1=tc1, ta1=ta1)
