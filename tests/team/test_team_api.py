from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.faker import fake
from app.team.models import Team, TeamMembership
from app.user.models import User
from tests.team.utils import create_test_team, create_test_teams
from tests.user.utils import create_test_users
from tests.utils import model_count


async def test_create_team(admin_client: AsyncClient, db: AsyncSession):
    """Should be able to create a new team"""

    users = await create_test_users(db, count=2)
    user_ids = [u.id for u in users]

    # Create valid team
    payload = {"name": fake.phrase(3), "user_ids": user_ids}

    res = await admin_client.post("/team/teams", json=payload)
    assert res.status_code == 201

    data = res.json()
    assert "id" in data
    assert await model_count(db, Team) == 1

    # Check created team
    rows = await db.execute(select(Team).where(Team.id == data["id"]))
    team = rows.scalar_one()
    assert team.name == payload["name"]
    assert len(team.memberships) == 2

    for mem in team.memberships:
        assert mem.user.id in user_ids


async def test_retrieve_team(admin_client: AsyncClient, db: AsyncSession):
    """Should be able to get a single team"""

    teams = await create_test_teams(db, count=3)

    # Get team that exists
    res = await admin_client.get(f"/team/teams/{teams[0].id}")
    assert res.status_code == 200

    data = res.json()
    assert "id" in data
    assert data["id"] == teams[0].id

    # Get team that doesn't exist
    res = await admin_client.get("/team/teams/100")
    assert res.status_code == 404

    data = res.json()
    assert "id" not in data


async def test_update_team(admin_client: AsyncClient, db: AsyncSession):
    """Should be able to update a single team"""

    ta, tb = await create_test_teams(db, count=2)

    ta_name_old = str(ta.name)
    ta_name_new = ta_name_old + " updated"
    tb_name_old = str(tb.name)

    payload = {"name": ta_name_new}
    res = await admin_client.patch(f"/team/teams/{ta.id}", json=payload)
    assert res.status_code == 200

    # Check the updated values
    await db.refresh(ta)
    await db.refresh(tb)

    assert ta.name == ta_name_new
    assert tb.name == tb_name_old


async def test_delete_team(admin_client: AsyncClient, db: AsyncSession):
    """Should be able to delete a team"""

    users = await create_test_users(db, count=3)
    ta = await create_test_team(db, users=users)
    tb = await create_test_team(db)

    res = await admin_client.delete(f"/team/teams/{ta.id}")
    assert res.status_code == 200

    data = res.json()
    assert "id" in data

    # Check db state
    assert await model_count(db, Team) == 1
    assert await model_count(db, TeamMembership) == 0
    assert await model_count(db, User) == 3

    await db.refresh(tb)
