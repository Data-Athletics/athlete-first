from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.user.models import User
from tests.utils import create_test_user, create_test_users


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


async def test_get_user(db: AsyncSession, client: AsyncClient):
    """Should get a single user"""

    # Initialize multiple users
    users = await create_test_users(db, count=5)

    # Retrieve a user that doesn't exist
    res = await client.get("/user/users/100")
    assert res.status_code == 404

    # Retrieve a user that does exist
    res = await client.get(f"/user/users/{users[0].id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == users[0].id


async def test_create_user(db: AsyncSession, client: AsyncClient):
    """Should create a new user"""

    # Create valid user
    payload = {
        "username": fake.user_name(),
    }

    res = await client.post("/user/users", json=payload)
    assert res.status_code == 201

    users = await db.execute(select(User))
    assert len(users.all()) == 1

    # Create invalid user (dup username)
    res = await client.post("/user/users", json=payload)
    assert res.status_code == 400

    users = await db.execute(select(User))
    assert len(users.all()) == 1


async def test_update_user(db: AsyncSession, client: AsyncClient):
    """Should update a user by their id"""

    users = await create_test_users(db, count=2)
    initial_usernames = (str(users[0].username), str(users[1].username))

    # Check valid input
    payload1 = {
        "username": initial_usernames[0] + "-updated",
    }

    res = await client.patch(f"/user/users/{users[0].id}", json=payload1)
    assert res.status_code == 200

    await db.refresh(users[0])
    assert users[0].username == payload1["username"]
    assert users[1].username == initial_usernames[1]

    # Check unique violation
    payload2 = {"username": initial_usernames[1]}

    res = await client.patch(f"/user/users/{users[0].id}", json=payload2)
    assert res.status_code == 400

    await db.refresh(users[0])
    assert users[0].username == payload1["username"]
    assert users[1].username == initial_usernames[1]


async def test_delete_user(db: AsyncSession, client: AsyncClient):
    """Should delete a user by their id"""

    users = await create_test_users(db, count=2)

    # Delete existing user
    res = await client.delete(f"/user/users/{users[0].id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == users[0].id

    users_1 = await db.execute(select(User))
    assert len(users_1.all()) == 1

    # Try deleting non-existant user
    res = await client.delete(f"/user/users/{users[0].id}")
    assert res.status_code == 404

    users_2 = await db.execute(select(User))
    assert len(users_2.all()) == 1
