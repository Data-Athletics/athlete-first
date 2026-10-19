from dataclasses import dataclass

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.models import Team, TeamMembership, TeamRoleType
from app.user.models import User
from tests.team.utils import create_test_team
from tests.user.utils import create_test_user, create_test_users


@dataclass
class TeamTestData:
    """Set of mock data for team testing"""

    # Group A
    team_a: Team
    users_a: list[User]
    athletes_a: list[TeamMembership]

    # Group B
    team_b: Team
    users_b: list[User]
    athletes_b: list[TeamMembership]


@pytest.fixture(scope="function", name="team_data")
async def team_data_fixture(db: AsyncSession) -> TeamTestData:
    """Setup initial data for a team"""

    # Group A
    users_a = await create_test_users(db, count=3)
    team_a = await create_test_team(db, user_ids=[u.id for u in users_a])
    athletes_a = team_a.memberships

    # Group B
    users_b = await create_test_users(db, count=3)
    team_b = await create_test_team(db, user_ids=[u.id for u in users_b])
    athletes_b = team_b.memberships

    return TeamTestData(
        team_a=team_a,
        users_a=users_a,
        athletes_a=athletes_a,
        team_b=team_b,
        users_b=users_b,
        athletes_b=athletes_b,
    )


async def test_list_team_memberships(
    admin_client: AsyncClient, db: AsyncSession, team_data: TeamTestData
):
    """Should be able to list team memberships for a team"""

    # Existing team
    team = team_data.team_a
    expected_user_ids = [u.id for u in team_data.users_a]

    res = await admin_client.get(f"/team/teams/{team.id}/memberships")
    assert res.status_code == 200

    data = res.json()
    assert isinstance(data, list)
    assert len(data) == len(expected_user_ids)

    for obj in data:
        assert obj["user_id"] in expected_user_ids

    # Non-existing team
    res = await admin_client.get("/team/teams/100/memberships")
    assert res.status_code == 404


async def test_create_team_membership(
    admin_client: AsyncClient, db: AsyncSession, team_data: TeamTestData
):
    """Should be able to create a team member"""

    team = team_data.team_a
    user = await create_test_user(db)
    initial_mem_count = len(team.memberships)

    # New user to team
    payload = {"user_id": user.id}
    res = await admin_client.post(f"/team/teams/{team.id}/memberships", json=payload)
    assert res.status_code == 201, res.content

    await db.refresh(team)
    assert len(team.memberships) == initial_mem_count + 1

    # Try to re-add user
    res = await admin_client.post(f"/team/teams/{team.id}/memberships", json=payload)
    assert res.status_code == 400

    await db.refresh(team)
    assert len(team.memberships) == initial_mem_count + 1

    # Try to add non-existant user
    payload = {"user_id": 100}
    res = await admin_client.post(f"/team/teams/{team.id}/memberships", json=payload)
    assert res.status_code == 422, res.content

    await db.refresh(team)
    assert len(team.memberships) == initial_mem_count + 1


async def test_retrieve_team_membership(
    admin_client: AsyncClient, db: AsyncSession, team_data: TeamTestData
):
    """Should be able to get details for a single team membership"""

    # Existing membership
    team = team_data.team_a
    membership = team_data.athletes_a[0]

    res = await admin_client.get(f"/team/teams/{team.id}/memberships/{membership.id}")
    assert res.status_code == 200

    data = res.json()
    assert data["id"] == membership.id

    # Non-existing membership
    res = await admin_client.get(f"/team/teams/{team.id}/memberships/100")
    assert res.status_code == 404


async def test_update_team_membership(
    admin_client: AsyncClient, db: AsyncSession, team_data: TeamTestData
):
    """Should be able to update a team membership"""

    team = team_data.team_a
    membership = team_data.athletes_a[0]

    # Update role
    payload = {"role": TeamRoleType.COACH}
    res = await admin_client.patch(
        f"/team/teams/{team.id}/memberships/{membership.id}", json=payload
    )
    assert res.status_code == 200

    await db.refresh(membership)
    assert membership.role == TeamRoleType.COACH

    # Try to update user id
    other_user = await create_test_user(db)
    old_user_id = int(membership.user_id)
    payload = {"user_id": other_user.id}
    res = await admin_client.patch(
        f"/team/teams/{team.id}/memberships/{membership.id}", json=payload
    )
    assert res.status_code == 422

    await db.refresh(membership)
    assert membership.user_id == old_user_id

    # Try to update team id
    other_team = await create_test_team(db)
    payload = {"team_id": other_team.id}
    res = await admin_client.patch(
        f"/team/teams/{team.id}/memberships/{membership.id}", json=payload
    )
    assert res.status_code == 422

    await db.refresh(membership)
    assert membership.team_id == team.id


async def test_delete_team_membership(
    admin_client: AsyncClient, db: AsyncSession, team_data: TeamTestData
):
    """Should be able to delete a team membership"""

    team = team_data.team_a
    membership = team_data.athletes_a[0]
    initial_mem_count = len(team.memberships)

    res = await admin_client.delete(
        f"/team/teams/{team.id}/memberships/{membership.id}"
    )
    assert res.status_code == 200

    await db.refresh(team)
    assert len(team.memberships) == initial_mem_count - 1
