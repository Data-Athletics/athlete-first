from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.services import authenticate_user
from app.core.faker import fake
from app.user.models import User
from tests.user.utils import create_test_user, create_test_users


async def test_list_users(
    db: AsyncSession, client: AsyncClient, admin_client: AsyncClient
):
    """Should list all users in the database"""

    # Setup users data
    user = await create_test_user(db)

    # Test unauthenticated request
    res = await client.get("/user/users")
    assert res.status_code == 401

    # Test authenticated request
    res = await admin_client.get("/user/users")
    assert res.status_code == 200

    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Last created user should appear first
    assert data[0]["id"] == user.id
    assert data[0]["is_active"] is True
    assert data[0]["can_login"] is False


async def test_get_user(
    db: AsyncSession, client: AsyncClient, admin_client: AsyncClient
):
    """Should get a single user"""

    # Initialize multiple users
    users = await create_test_users(db, count=5)

    # Unauthenticated request + existing user
    res = await client.get(f"/user/users/{users[0].id}")
    assert res.status_code == 401

    # Unauthenticated request + non-existing user
    res = await client.get("/user/users/100")
    assert res.status_code == 401

    # Retrieve a user that doesn't exist
    res = await admin_client.get("/user/users/100")
    assert res.status_code == 404

    # Retrieve a user that does exist
    res = await admin_client.get(f"/user/users/{users[0].id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == users[0].id


async def test_create_user(
    db: AsyncSession, client: AsyncClient, admin_client: AsyncClient
):
    """Should create a new user"""

    # Create valid user
    payload = {
        "username": fake.username(),
        "password": "changeme",
    }

    # Unauthenticated request
    res = await client.post("/user/users", json=payload)
    assert res.status_code == 401

    # Authenticated request
    res = await admin_client.post("/user/users", json=payload)
    assert res.status_code == 201

    users = (await db.execute(select(User))).scalars().all()
    assert len(users) == 2

    # Check the user that was created
    db_user = next(user for user in users if user.id == res.json()["id"])
    assert db_user.hashed_password is not None
    assert db_user.hashed_password != payload["password"]

    # Create invalid user (dup username)
    res = await admin_client.post("/user/users", json=payload)
    assert res.status_code == 400

    users = await db.execute(select(User))
    assert len(users.all()) == 2


async def test_create_user_valid_password(db: AsyncSession, admin_client: AsyncClient):
    """Should only create a user if the password meets requirements"""

    # Allow password to be null
    payload = {"username": fake.username()}
    res = await admin_client.post("/user/users", json=payload)
    assert res.status_code == 201

    # Prevent password from being too short
    payload = {"username": fake.username(), "password": "12345"}
    res = await admin_client.post("/user/users", json=payload)
    assert res.status_code == 422

    # Valid password length
    payload = {"username": fake.username(), "password": "123456"}
    res = await admin_client.post("/user/users", json=payload)
    assert res.status_code == 201


async def test_update_user(
    db: AsyncSession, client: AsyncClient, admin_client: AsyncClient
):
    """Should update a user by their id"""

    users = await create_test_users(db, count=2, hashed_password="some-hash")
    initial_usernames = (str(users[0].username), str(users[1].username))
    initial_weights = (users[0].weight, users[1].weight)

    payload1 = {
        "username": initial_usernames[0] + "-updated",
        "weight": 180.0,
    }

    # Unauthenticated request
    res = await client.patch(f"/user/users/{users[0].id}", json=payload1)
    assert res.status_code == 401

    # Non-existant user
    res = await admin_client.patch("/user/users/100", json=payload1)
    assert res.status_code == 404

    # Check valid input
    res = await admin_client.patch(f"/user/users/{users[0].id}", json=payload1)
    assert res.status_code == 200
    data = res.json()
    assert "password" not in data
    assert "hashed_password" not in data

    await db.refresh(users[0])
    assert users[0].username == payload1["username"]
    assert users[0].weight == payload1["weight"]
    assert users[1].username == initial_usernames[1]
    assert users[1].weight == initial_weights[1]

    # Check unique violation
    payload2 = {"username": initial_usernames[1]}

    res = await admin_client.patch(f"/user/users/{users[0].id}", json=payload2)
    assert res.status_code == 400

    await db.refresh(users[0])
    assert users[0].username == payload1["username"]
    assert users[0].weight == payload1["weight"]
    assert users[1].username == initial_usernames[1]
    assert users[1].weight == initial_weights[1]

    # Cannot update another user's password
    payload3 = {
        "password": "changeme",
        "hashed_password": "changeme",
    }

    res = await admin_client.patch(f"/user/users/{users[0].id}", json=payload3)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    password_before = str(users[0].hashed_password)
    await db.refresh(users[0])
    assert users[0].hashed_password == password_before


async def test_delete_user(
    db: AsyncSession, client: AsyncClient, admin_client: AsyncClient
):
    """Should delete a user by their id"""

    # Create 2 additional users
    users = await create_test_users(db, count=2)

    # Unauthenticated user
    res = await client.delete(f"/user/users/{users[0].id}")
    assert res.status_code == 401

    # Delete existing user
    res = await admin_client.delete(f"/user/users/{users[0].id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == users[0].id

    users_1 = await db.execute(select(User))
    assert len(users_1.all()) == 2

    # Try deleting non-existant user
    res = await admin_client.delete(f"/user/users/{users[0].id}")
    assert res.status_code == 404

    users_2 = await db.execute(select(User))
    assert len(users_2.all()) == 2


async def test_update_current_user(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should be able to update the current user"""

    # TODO: Prevent non-admins from setting themselves as admin

    another_user = await create_test_user(db)

    # Set valid username
    payload = {"username": current_admin.username + "-updated"}
    res = await admin_client.patch("/user/me", json=payload)
    assert res.status_code == 200

    # Verify the data was saved
    await db.refresh(current_admin)
    assert current_admin.username == payload["username"]
    old_username = payload["username"]

    # Set duplicate username
    payload = {"username": another_user.username}
    res = await admin_client.patch("/user/me", json=payload)
    assert res.status_code == 400

    # Verify the old username is still set
    await db.refresh(current_admin)
    assert current_admin.username == old_username


async def test_update_current_user_valid_password(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should only be able to update password with a valid password"""

    # Prevent setting password that's too short
    payload = {"password": "12345"}
    res = await admin_client.patch("/user/me", json=payload)
    assert res.status_code == 422

    # Allow setting password with valid length
    payload = {"password": "123456"}
    res = await admin_client.patch("/user/me", json=payload)
    assert res.status_code == 200, res.content

    # Verify the password saved
    user = await authenticate_user(db, current_admin.username, payload["password"])
    assert user is not None
