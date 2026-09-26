from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.user.utils import create_test_user


async def test_user_login(db: AsyncSession, client: AsyncClient):
    """Should be able to login a valid user"""

    user = await create_test_user(db, username="test", password="changeme")

    # Unable to login with wrong password
    payload = {"username": "test", "password": "wrong-password"}
    res = await client.post("/auth/token", json=payload)
    assert res.status_code == 400
    data = res.json()
    assert "access_token" not in data

    # Unable to login with invalid username
    payload = {"username": "noexist", "password": "changeme"}
    res = await client.post("/auth/token", json=payload)
    assert res.status_code == 400
    data = res.json()
    assert "access_token" not in data

    # User can successfully login and get an access token
    payload = {"username": "test", "password": "changeme"}
    res = await client.post("/auth/token", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "expires_in" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["access_token"] is not None

    # User can use the access token for authenticated routes
    res = await client.get(
        "/user/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert res.status_code == 200

    data = res.json()
    assert "id" in data
    assert data["id"] == user.id
