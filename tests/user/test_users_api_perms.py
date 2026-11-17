from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.user.models import User
from tests.team.utils import create_test_team
from tests.user.utils import create_test_user, create_test_users
from tests.utils import model_count


async def test_staff_create_users(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create users"""

    assert await model_count(db, User) == 1

    payload = {"username": fake.username(), "password": "changeme", "name": fake.name()}

    # Rejected if regular user
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 403
    assert await model_count(db, User) == 1

    # Coaches that are not staff should not be able to create users
    await create_test_team(db, coach_user_ids=[current_user.id])
    await db.refresh(current_user)

    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 403
    assert await model_count(db, User) == 1

    # Staff can create users
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201
    assert await model_count(db, User) == 2

    # Inactive staff cannot create users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 401
    assert await model_count(db, User) == 2

    # Admins can create users
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201
    assert await model_count(db, User) == 3

    # Inactive admins cannot create users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 401
    assert await model_count(db, User) == 3


async def test_staff_list_users(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create users"""

    u1 = await create_test_user(db)  # Same team
    _u2 = await create_test_user(db)  # Not in team

    # Getting should return 403 for regular user
    res = await user_client.get("/user/users")
    assert res.status_code == 403

    # Coaches that are not staff should able to see users in their team
    await create_test_team(db, coach_user_ids=[current_user.id], user_ids=[u1.id])
    await db.refresh(current_user)
    await db.refresh(u1)

    res = await user_client.get("/user/users")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 2
    assert data[0]["id"] == u1.id  # Most recently created user

    # Staff should be able to list all users
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/user/users")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 3

    # Inactive staff cannot list users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/user/users")
    assert res.status_code == 401

    # Admins can list all users
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/user/users")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 3

    # Inactive admins cannot get users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/user/users")
    assert res.status_code == 401


async def test_staff_retrieve_users(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create users"""

    u1 = await create_test_user(db)  # Same team
    u2 = await create_test_user(db)  # Not in team

    # Getting should return 403 for regular user
    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 403

    # Coaches that are not staff should able to see user in their team
    await create_test_team(db, coach_user_ids=[current_user.id], user_ids=[u1.id])
    await db.refresh(current_user)
    await db.refresh(u1)

    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 200

    # Staff should be able to get users
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/user/users/{u2.id}")
    assert res.status_code == 200

    # Inactive staff cannot get users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/user/users/{u2.id}")
    assert res.status_code == 401

    # Admins can get users
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/user/users/{u2.id}")
    assert res.status_code == 200

    # Inactive admins cannot get users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/user/users/{u2.id}")
    assert res.status_code == 401


async def test_staff_update_users(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create users"""

    target_user = await create_test_user(db)

    payload = {"name": fake.name()}
    assert target_user.name != payload["name"]

    # Update should return 403 for regular user (method checked before user id)
    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 403

    await db.refresh(target_user)
    assert target_user.name != payload["name"]

    # Coaches that are not staff should be rejected with 403
    await create_test_team(
        db, coach_user_ids=[current_user.id], user_ids=[target_user.id]
    )
    await db.refresh(current_user)
    await db.refresh(target_user)

    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 403

    await db.refresh(target_user)
    assert target_user.name != payload["name"]

    # Staff should be able to update users
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(target_user)
    assert target_user.name == payload["name"]

    # Inactive staff cannot update users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"name": payload["name"] + " updated"}
    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(target_user)
    assert target_user.name != payload["name"]

    # Admins can update users
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(target_user)
    assert target_user.name == payload["name"]

    # Inactive admins cannot update users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"name": payload["name"] + " updated"}
    res = await user_client.patch(f"/user/users/{target_user.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(target_user)
    assert target_user.name != payload["name"]


async def test_staff_delete_users(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create users"""

    # u1 in same team, others not
    u1, u2, u3, u4 = await create_test_users(db, count=4)

    # Getting should return 403 for regular user (method checked before querying user)
    res = await user_client.delete(f"/user/users/{u1.id}")
    assert res.status_code == 403

    assert await model_count(db, User, where=(User.id == u1.id)) == 1

    # Coaches that are not staff should not be able to delete users in their team
    await create_test_team(db, coach_user_ids=[current_user.id], user_ids=[u1.id])
    await db.refresh(current_user)
    await db.refresh(u1)

    res = await user_client.delete(f"/user/users/{u1.id}")
    assert res.status_code == 403

    assert await model_count(db, User, where=(User.id == u1.id)) == 1

    # Staff should be able to delete users
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/user/users/{u2.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == u2.id)) == 0

    # Inactive staff cannot delete users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/user/users/{u3.id}")
    assert res.status_code == 401

    assert await model_count(db, User, where=(User.id == u3.id)) == 1

    # Admins can delete users
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/user/users/{u3.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == u3.id)) == 0

    # Inactive admins cannot delete users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/user/users/{u4.id}")
    assert res.status_code == 401

    assert await model_count(db, User, where=(User.id == u4.id)) == 1
