from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.team.models import Team
from app.user.models import User
from tests.team.utils import create_test_team, create_test_teams
from tests.utils import model_count


async def test_create_teams_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create teams"""

    assert await model_count(db, Team) == 0

    payload = {"name": fake.phrase()}

    # Rejected if regular user
    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"
    assert await model_count(db, Team) == 0

    # Coaches that are not staff should not be able to create teams
    await create_test_team(db, coach_user_ids=[current_user.id])
    await db.refresh(current_user)

    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"
    assert await model_count(db, Team) == 1

    # Staff can create teams
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 201
    assert await model_count(db, Team) == 2

    # Inactive staff cannot create teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["name"] = fake.phrase()
    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 401
    assert await model_count(db, Team) == 2

    # Admins can create teams
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 201
    assert await model_count(db, Team) == 3

    # Inactive admins cannot create users
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["name"] = fake.phrase()
    res = await user_client.post("/team/teams", json=payload)
    assert res.status_code == 401
    assert await model_count(db, Team) == 3


async def test_list_teams_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to list teams"""

    t1 = await create_test_team(db, coach_user_ids=[current_user.id])
    t2 = await create_test_team(db, user_ids=[current_user.id])
    t3 = await create_test_team(db)

    # Getting should return list of teams the user is in
    res = await user_client.get("/team/teams")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 2

    for team_data in data:
        assert team_data["id"] in [t1.id, t2.id]
        assert team_data["membership"] is not None
        assert team_data["membership"]["user_id"] == current_user.id
        assert team_data["membership"]["team_id"] == team_data["id"]

    # Staff should be able to list all teams
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/team/teams")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 3

    for team_data in data:
        if team_data["id"] == t3.id:
            assert team_data["membership"] is None
        else:
            assert team_data["membership"] is not None
            assert team_data["membership"]["user_id"] == current_user.id
            assert team_data["membership"]["team_id"] == team_data["id"]

    # Inactive staff cannot list teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/team/teams")
    assert res.status_code == 401

    # Admins can list all teams
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/team/teams")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == 3

    for team_data in data:
        if team_data["id"] == t3.id:
            assert team_data["membership"] is None
        else:
            assert team_data["membership"] is not None
            assert team_data["membership"]["user_id"] == current_user.id
            assert team_data["membership"]["team_id"] == team_data["id"]

    # Inactive admins cannot get teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get("/team/teams")
    assert res.status_code == 401


async def test_retrieve_teams_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Members of a team should be able to get team details"""

    t1 = await create_test_team(db, coach_user_ids=[current_user.id])
    t2 = await create_test_team(db, user_ids=[current_user.id])
    t3 = await create_test_team(db)

    # Athletes can get info on their team
    res = await user_client.get(f"/team/teams/{t2.id}")
    assert res.status_code == 200

    # Coaches can get info on their team
    res = await user_client.get(f"/team/teams/{t1.id}")
    assert res.status_code == 200

    # Non-members of a team cannot retrieve the team's info
    res = await user_client.get(f"/team/teams/{t3.id}")
    assert res.status_code == 404

    # Staff should be able to get info on any team
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}")
    assert res.status_code == 200

    # Inactive staff cannot get any team
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}")
    assert res.status_code == 401

    # Admins can get any team
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}")
    assert res.status_code == 200

    # Inactive admins cannot get any team
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}")
    assert res.status_code == 401


async def test_update_teams_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to update teams"""

    target_team = await create_test_team(db)

    payload = {"name": fake.phrase()}
    assert target_team.name != payload["name"]

    # Update should return 403 for regular user (method checked before team id)
    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(target_team)
    assert target_team.name != payload["name"]

    # Coaches that are not staff should be rejected with 403
    target_team = await create_test_team(db, coach_user_ids=[current_user.id])
    await db.refresh(current_user)

    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    await db.refresh(target_team)
    assert target_team.name != payload["name"]

    # Staff should be able to update teams
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(target_team)
    assert target_team.name == payload["name"]

    # Inactive staff cannot update teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"name": payload["name"] + " updated"}
    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(target_team)
    assert target_team.name != payload["name"]

    # Admins can update teams
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 200

    await db.refresh(target_team)
    assert target_team.name == payload["name"]

    # Inactive admins cannot update teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"name": payload["name"] + " updated"}
    res = await user_client.patch(f"/team/teams/{target_team.id}", json=payload)
    assert res.status_code == 401

    await db.refresh(target_team)
    assert target_team.name != payload["name"]


async def test_delete_teams_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to delete teams"""

    t1 = await create_test_team(db, coach_user_ids=[current_user.id])
    t2 = await create_test_team(db, user_ids=[current_user.id])
    t3, t4, t5 = await create_test_teams(db, count=3)

    # Regular members should not be able to delete a team
    res = await user_client.delete(f"/team/teams/{t2.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    assert await model_count(db, Team, where=(Team.id == t2.id)) == 1

    # Coaches should not be able to delete a team
    res = await user_client.delete(f"/team/teams/{t1.id}")
    assert res.status_code == 403
    assert res.json()["reason"] == "staff_only"

    assert await model_count(db, Team, where=(Team.id == t1.id)) == 1

    # Staff should be able to delete teams
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t3.id}")
    assert res.status_code == 200

    assert await model_count(db, Team, where=(Team.id == t3.id)) == 0

    # Inactive staff cannot delete teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t4.id}")
    assert res.status_code == 401

    assert await model_count(db, Team, where=(Team.id == t4.id)) == 1

    # Admins can delete teams
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t4.id}")
    assert res.status_code == 200

    assert await model_count(db, Team, where=(Team.id == t4.id)) == 0

    # Inactive admins cannot delete teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t5.id}")
    assert res.status_code == 401

    assert await model_count(db, Team, where=(Team.id == t5.id)) == 1
