from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.user.models import User
from tests.team.utils import create_test_team
from tests.user.utils import UserPermsData, create_test_user, create_test_users
from tests.utils import model_count


async def test_create_users_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Only staff and admins should be able to create users"""

    user_start_count = await model_count(db, User)

    payload: dict[str, Any] = {
        "username": fake.username(),
        "password": "changeme",
        "name": fake.name(),
    }

    # Rejected if regular user
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"
    assert await model_count(db, User) == user_start_count

    # Coaches that are not staff should not be able to create users
    await user_perms_data.set_coach(db, current_user)
    assert res.json()["reason"] == "staff_only"
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 403
    assert await model_count(db, User) == user_start_count

    # Staff can create users
    await user_perms_data.set_staff(db, current_user)

    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201
    assert await model_count(db, User) == user_start_count + 1

    # Staff can create other staff
    payload["is_staff"] = True
    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201, res.content
    assert res.json()["is_staff"] is True
    assert await model_count(db, User) == user_start_count + 2

    # Staff cannot create admins
    payload["is_admin"] = True
    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"
    assert await model_count(db, User) == user_start_count + 2

    # Inactive staff cannot create users
    await user_perms_data.set_inactive(db, current_user)

    payload["is_admin"] = None
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 401
    assert await model_count(db, User) == user_start_count + 2

    await user_perms_data.set_active(db, current_user)

    # Admins can create users
    await user_perms_data.set_admin(db, current_user)

    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201
    assert await model_count(db, User) == user_start_count + 3

    # Admins can create other admins
    payload["is_admin"] = True
    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 201
    assert await model_count(db, User) == user_start_count + 4

    # Inactive admins cannot create users
    await user_perms_data.set_inactive(db, current_user)

    payload["username"] = fake.username()
    res = await user_client.post("/user/users", json=payload)
    assert res.status_code == 401
    assert await model_count(db, User) == user_start_count + 4


async def test_list_users_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Listing users should be restricted to coaches and staff"""

    u1 = await create_test_user(db)  # Same team
    _u2 = await create_test_user(db)  # Not in team

    # Getting should return 403 for regular user
    res = await user_client.get("/user/users")
    assert res.status_code == 403
    assert res.json()["reason"] == "coaches_only"

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


async def test_retrieve_users_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Retrieving users should be restricted based on role"""

    u1 = user_perms_data.u1
    ta1 = user_perms_data.ta1

    # Getting should return 403 for regular user
    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "coaches_only"

    # Regular users cannot see themselves
    res = await user_client.get(f"/user/users/{current_user.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "coaches_only"

    # Coaches that are not staff should able to see user in their team
    await user_perms_data.set_coach(db, current_user)
    await db.refresh(current_user)

    res = await user_client.get(f"/user/users/{ta1.id}")
    assert res.status_code == 200

    # Coaches cannot see users not in their team
    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 404

    # Coaches can see themselves
    res = await user_client.get(f"/user/users/{current_user.id}")
    assert res.status_code == 200

    # Staff should be able to get users
    await user_perms_data.set_staff(db, current_user)

    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 200

    # Inactive staff cannot get users
    await user_perms_data.set_inactive(db, current_user)

    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 401

    await user_perms_data.set_active(db, current_user)  # Reset to active

    # Admins can get users
    await user_perms_data.set_admin(db, current_user)

    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 200

    # Inactive admins cannot get users
    await user_perms_data.set_inactive(db, current_user)

    res = await user_client.get(f"/user/users/{u1.id}")
    assert res.status_code == 401


async def test_update_users_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Only staff and admins should be able to update users"""

    u1 = user_perms_data.u1
    ta1 = user_perms_data.ta1

    payload = {"name": fake.name()}
    assert u1.name != payload["name"]

    # Update should return 403 for regular user
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(u1)
    assert u1.name != payload["name"]

    # Update returns forbidden for non-existing user (method checked before user id)
    res = await user_client.patch("/user/users/100", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    # Regular users cannot update themselves
    res = await user_client.patch(f"/user/users/{current_user.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(current_user)
    assert current_user.name != payload["name"]

    # Coaches that are not staff should be rejected with 403
    await user_perms_data.set_coach(db, current_user)

    res = await user_client.patch(f"/user/users/{ta1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(ta1)
    assert ta1.name != payload["name"]

    # Staff should be able to update users
    await user_perms_data.set_staff(db, current_user)

    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(u1)
    assert u1.name == payload["name"]

    # Staff can set another user's password
    hashed_pass_before = u1.hashed_password
    payload = {"password": "changeme"}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 200
    assert "password" not in res.json()

    await db.refresh(u1)
    assert u1.hashed_password != hashed_pass_before

    # Inactive staff cannot update users
    await user_perms_data.set_inactive(db, current_user)

    payload = {"name": u1.name + " updated"}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(u1)
    assert u1.name != payload["name"]

    await user_perms_data.set_active(db, current_user)  # Reset back to active

    # Admins can update users
    await user_perms_data.set_admin(db, current_user)

    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(u1)
    assert u1.name == payload["name"]

    # Inactive admins cannot update users
    await user_perms_data.set_inactive(db, current_user)

    payload = {"name": payload["name"] + " updated"}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(u1)
    assert u1.name != payload["name"]


async def test_user_privilege_escalation(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """A user should not be able to elevate their own or another user's permissions"""

    u1 = user_perms_data.u1

    # Normal user should not be able to set someone as staff
    payload = {"is_staff": True}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(u1)
    assert u1.is_staff is False

    # Normal user should not be able to set themselves as staff
    res = await user_client.patch(f"/user/users/{current_user.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(current_user)
    assert current_user.is_staff is False

    # Normal users cannot set other users as inactive
    payload = {"is_active": False}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(u1)
    assert u1.is_active is True

    # Coaches cannot set users as inactive
    await create_test_team(db, coach_user_ids=[current_user.id], user_ids=[u1.id])
    await db.refresh(current_user)
    await db.refresh(u1)

    payload = {"is_active": False}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(u1)
    assert u1.is_active is True


async def test_staff_privilege_escalation(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Staff should not be able to promote themselves or demote admins"""

    u1 = user_perms_data.u1
    s1 = user_perms_data.s1
    a1 = user_perms_data.a1

    # Staff can set other users as staff
    await user_perms_data.set_staff(db, current_user)

    payload = {"is_staff": True}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 200, res.content

    await db.refresh(u1)
    assert u1.is_staff is True

    await user_perms_data.set_user(db, u1)  # Reset user

    # Staff cannot, however, set themselves as admin
    payload = {"is_admin": True}
    res = await user_client.patch(f"/user/users/{current_user.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    await db.refresh(current_user)
    assert current_user.is_admin is False

    # Staff cannot set other user as admin
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    await db.refresh(u1)
    assert u1.is_admin is False

    # Staff can demote themselves
    payload = {"is_staff": False}
    res = await user_client.patch(f"/user/users/{current_user.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(current_user)
    assert current_user.is_staff is False

    await user_perms_data.set_staff(db, current_user)  # Reset current user to staff

    # Staff can also demote other users from staff
    payload = {"is_staff": False}
    res = await user_client.patch(f"/user/users/{s1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(s1)
    assert s1.is_staff is False

    await user_perms_data.set_staff(db, s1)  # Reset staff user

    # Staff cannot demote admins
    payload = {"is_admin": False}
    res = await user_client.patch(f"/user/users/{a1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    await db.refresh(a1)
    assert a1.is_admin is True

    # Staff cannot set admins as inactive
    payload = {"is_active": False}
    res = await user_client.patch(f"/user/users/{a1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    await db.refresh(a1)
    assert a1.is_active is True

    # Staff can set another staff's password
    hashed_pass_before = s1.hashed_password
    payload = {"password": "changeme"}
    res = await user_client.patch(f"/user/users/{s1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(s1)
    assert s1.hashed_password != hashed_pass_before

    # Staff cannot change an admin's password
    hashed_pass_before = a1.hashed_password
    payload = {"password": "changeme"}
    res = await user_client.patch(f"/user/users/{a1.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    await db.refresh(a1)
    assert a1.hashed_password == hashed_pass_before


async def test_admin_privilege_escalation(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Admins should be able to demote other users"""

    u1 = user_perms_data.u1
    a1 = user_perms_data.a1

    await user_perms_data.set_admin(db, current_user)

    # Admins can set other users as admin
    payload = {"is_admin": True}
    res = await user_client.patch(f"/user/users/{u1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(u1)
    assert u1.is_admin is True

    await user_perms_data.set_user(db, u1)  # Reset user

    # Admins can demote themselves
    payload = {"is_admin": False}
    res = await user_client.patch(f"/user/users/{current_user.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(current_user)
    assert current_user.is_admin is False

    await user_perms_data.set_admin(db, current_user)  # Reset current user to admin

    # Admins can demote other admins
    res = await user_client.patch(f"/user/users/{a1.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(a1)
    assert a1.is_admin is False


async def test_delete_users_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    user_perms_data: UserPermsData,
):
    """Only staff and admins should be able to delete users"""

    u1 = user_perms_data.u1
    u2, u3, u4 = await create_test_users(db, count=3)
    s1 = user_perms_data.s1
    a1 = user_perms_data.a1
    ta1 = user_perms_data.ta1

    # Getting should return 403 for regular user (method checked before querying user)
    res = await user_client.delete(f"/user/users/{u1.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    assert await model_count(db, User, where=(User.id == u1.id)) == 1

    # Coaches that are not staff should not be able to delete users in their team
    await user_perms_data.set_coach(db, current_user)

    res = await user_client.delete(f"/user/users/{ta1.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    assert await model_count(db, User, where=(User.id == ta1.id)) == 1
    await user_perms_data.remove_from_team(db, current_user)

    # Staff should be able to delete users
    await user_perms_data.set_staff(db, current_user)

    res = await user_client.delete(f"/user/users/{u2.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == u2.id)) == 0

    # Staff should be able to delete other staff
    res = await user_client.delete(f"/user/users/{s1.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == s1.id)) == 0

    # Staff cannot delete admins
    res = await user_client.delete(f"/user/users/{a1.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "admin_only"

    assert await model_count(db, User, where=(User.id == a1.id)) == 1

    # Inactive staff cannot delete users
    await user_perms_data.set_inactive(db, current_user)

    res = await user_client.delete(f"/user/users/{u3.id}")
    assert res.status_code == 401
    assert await model_count(db, User, where=(User.id == u3.id)) == 1

    await user_perms_data.set_active(db, current_user)

    # Admins can delete users
    await user_perms_data.set_admin(db, current_user)

    res = await user_client.delete(f"/user/users/{u3.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == u3.id)) == 0

    # Admins can delete other admins
    res = await user_client.delete(f"/user/users/{a1.id}")
    assert res.status_code == 200

    assert await model_count(db, User, where=(User.id == a1.id)) == 0

    # Inactive admins cannot delete users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/user/users/{u4.id}")
    assert res.status_code == 401

    assert await model_count(db, User, where=(User.id == u4.id)) == 1
