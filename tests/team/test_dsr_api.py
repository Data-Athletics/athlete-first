from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.services import get_effective_membership_dsp
from app.user.models import User
from tests.team.utils import create_test_team


async def test_get_default_dsr(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should be able to get the default data sharing requirements"""

    team = await create_test_team(db, user_ids=[current_admin.id])

    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-requirements")
    assert res.status_code == 200

    # Check default attributes
    data = res.json()
    assert data["bpm_shared"] is None
    assert data["calories_shared"] is None
    assert data["respiratory_rate_shared"] is None
    assert data["hrv_shared"] is None
    assert data["effort_shared"] is None
    assert data["skin_temp_delta_shared"] is None


async def test_set_dsr(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should be able to update a teams data sharing requirements"""

    team = await create_test_team(db, user_ids=[current_admin.id])

    # Set 2 fields as required
    payload = {"bpm_shared": True, "calories_shared": True}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 200

    # Re-fetch the dsr
    res = await admin_client.get(f"/team/teams/{team.id}/data-sharing-requirements")
    assert res.status_code == 200

    # Check default attributes
    data = res.json()
    assert data["bpm_shared"] is True
    assert data["calories_shared"] is True
    assert data["respiratory_rate_shared"] is None
    assert data["hrv_shared"] is None
    assert data["effort_shared"] is None
    assert data["skin_temp_delta_shared"] is None


async def test_set_dsr_past_existing_dsp(
    db: AsyncSession, admin_client: AsyncClient, current_admin: User
):
    """Should allow setting requirements not aligned with a current policy"""

    team = await create_test_team(db, user_ids=[current_admin.id])
    membership = team.memberships[0]

    # User creates dsp with bpm explicitly not shared
    payload = {"bpm_shared": False}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 200

    await db.refresh(membership)
    dsp = get_effective_membership_dsp(membership)
    assert dsp.bpm_shared is False

    # Coach then sets the requirements to require bpm
    payload = {"bpm_shared": True}
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 200

    # The policy shouldn't change, but should show an invalid field
    await db.refresh(membership)
    dsp = get_effective_membership_dsp(membership)
    assert len(dsp.invalid_fields) == 1
    assert dsp.invalid_fields[0] == "bpm_shared"

    # Making the field valid again
    res = await admin_client.put(
        f"/team/teams/{team.id}/data-sharing-policy", json=payload
    )
    assert res.status_code == 200

    await db.refresh(membership)
    dsp = get_effective_membership_dsp(membership)
    assert len(dsp.invalid_fields) == 0
