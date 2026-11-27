from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.models import User
from tests.team.utils import TeamMembershipsData


async def test_retrieve_dsr_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """All team members and staff can see a team's data sharing requirements"""

    t1, t2, t3 = team_memberships_data.get_teams()
    assert t1.dsr is not None
    assert t2.dsr is not None
    assert t3.dsr is not None

    # Non-members cannot see the DSR
    res = await user_client.get(f"/team/teams/{t3.id}/data-sharing-requirements")
    assert res.status_code == 404

    # Athletes can see a team's DSR
    res = await user_client.get(f"/team/teams/{t2.id}/data-sharing-requirements")
    assert res.status_code == 200

    # Coaches can see a team's DSR
    res = await user_client.get(f"/team/teams/{t1.id}/data-sharing-requirements")
    assert res.status_code == 200

    # Staff can see any team's DSR
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/data-sharing-requirements")
    assert res.status_code == 200

    # Admins can also see any team's DSR
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/data-sharing-requirements")
    assert res.status_code == 200


async def test_update_dsr_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """Only coaches and staff can set a team's DSR"""

    t1, t2, t3 = team_memberships_data.get_teams()
    assert t1.dsr is not None
    assert t2.dsr is not None
    assert t3.dsr is not None

    payload = {"bpm_shared": True}

    # Non-members cannot set a team's DSR
    res = await user_client.put(
        f"/team/teams/{t3.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 404

    await db.refresh(t3.dsr)
    assert t3.dsr.content.get("bpm_shared", None) is None

    # Athletes cannot set a team's DSR
    res = await user_client.put(
        f"/team/teams/{t2.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 403

    await db.refresh(t2.dsr)
    assert t2.dsr.content.get("bpm_shared", None) is None

    # Coaches that are not staff can set a team's DSR
    res = await user_client.put(
        f"/team/teams/{t1.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 200

    await db.refresh(t1.dsr)
    assert t1.dsr.content["bpm_shared"] is True

    # Staff can set any team's DSR
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.put(
        f"/team/teams/{t3.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 200

    await db.refresh(t3.dsr)
    assert t3.dsr.content["bpm_shared"] is True

    # Admins can set any team's DSR
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    payload["calories_shared"] = True
    res = await user_client.put(
        f"/team/teams/{t3.id}/data-sharing-requirements", json=payload
    )
    assert res.status_code == 200

    await db.refresh(t3.dsr)
    assert t3.dsr.content["calories_shared"] is True
