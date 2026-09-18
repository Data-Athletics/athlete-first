from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import create_test_user


async def test_list_users(db: AsyncSession, client: AsyncClient):
    """Should list all users in the database"""

    # Setup users data
    user = await create_test_user(db)

    # Test api
    res = await client.get("/user/users")
    assert res.status_code == 200

    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == user.id
    assert data[0]["is_active"] is True
    assert data[0]["can_login"] is False
