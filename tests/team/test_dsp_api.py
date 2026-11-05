from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.models import TeamDsr
from app.team.services import get_effective_membership_dsp
from app.user.models import User
from tests.team.utils import create_test_team


async def test_get_default_dsp(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should be able to get the default data share policy for a team"""

    team = await create_test_team(db, user_ids=[current_admin.id])

    # User hasn't accepted policy yet
    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-policy")
    assert res.status_code == 404

    # User creates dsp with default settings
    res = await admin_client.put(f"/team/teams/{team.id}/data-sharing-policy", json={})
    assert res.status_code == 200

    # Then the user queries the dsp again
    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-policy")
    assert res.status_code == 200, res.content

    # Check default attributes
    data = res.json()
    assert data["bpm_shared"] is True
    assert data["calories_shared"] is True
    assert data["respiratory_rate_shared"] is True
    assert data["hrv_shared"] is True
    assert data["effort_shared"] is True
    assert data["skin_temp_delta_shared"] is True


async def test_set_dsp(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should allow a user to update their dsp for a team"""

    team = await create_test_team(db, user_ids=[current_admin.id])

    # User hasn't accepted policy yet
    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-policy")
    assert res.status_code == 404

    # User creates dsp with default settings
    res = await admin_client.put(f"/team/teams/{team.id}/data-sharing-policy", json={})
    assert res.status_code == 200

    # Then the user queries the dsp again
    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-policy")
    assert res.status_code == 200

    # The user then updates the dsp
    payload = {"bpm_shared": False, "calories_shared": False, "hrv_shared": True}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 200

    data = res.json()
    assert data["bpm_shared"] is False
    assert data["calories_shared"] is False
    assert data["respiratory_rate_shared"] is True
    assert data["hrv_shared"] is True
    assert data["effort_shared"] is True
    assert data["skin_temp_delta_shared"] is True

    # Update dsp again, overwriting values with None
    payload = {"calories_shared": False, "hrv_shared": True}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 200

    data = res.json()
    assert data["bpm_shared"] is True  # Reverts back to default
    assert data["calories_shared"] is False
    assert data["respiratory_rate_shared"] is True
    assert data["hrv_shared"] is True
    assert data["effort_shared"] is True
    assert data["skin_temp_delta_shared"] is True


async def test_set_dsp_past_min(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should reject updates to dsp that go under requirements"""

    team = await create_test_team(db, user_ids=[current_admin.id])

    dsr = TeamDsr(
        team_id=team.id,
        content={"bpm_shared": True, "calories_shared": False, "effort_shared": True},
    )
    db.add(dsr)
    await db.commit()
    await db.refresh(team)

    membership = team.memberships[0]

    # User creates dsp with default settings
    res = await admin_client.put(f"/team/teams/{team.id}/data-sharing-policy", json={})
    assert res.status_code == 200

    data = res.json()
    assert data["bpm_shared"] is True
    assert data["calories_shared"] is False
    assert data["respiratory_rate_shared"] is True
    assert data["effort_shared"] is True

    # User attempts to override false value
    payload = {"calories_shared": True}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 400

    await db.refresh(membership)
    dsp = get_effective_membership_dsp(membership)
    assert dsp.calories_shared is False

    # User attempts to override true value
    payload = {"bpm_shared": False}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 400

    await db.refresh(membership)
    dsp = get_effective_membership_dsp(membership)
    assert dsp.bpm_shared is True
