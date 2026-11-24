from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.models import TeamMembership, TeamRoleType
from app.user.models import User
from tests.team.utils import TeamMembershipsData, create_test_team
from tests.user.utils import create_test_users
from tests.utils import model_count


async def test_create_team_members_perms(
    db: AsyncSession, user_client: AsyncClient, current_user: User
):
    """Only staff and admins should be able to create team members"""

    t1 = await create_test_team(db, coach_user_ids=[current_user.id])
    t2 = await create_test_team(db, user_ids=[current_user.id])
    t3 = await create_test_team(db)
    u1, u2, u3 = await create_test_users(db, count=3)

    assert await model_count(db, TeamMembership) == 2

    payload = {"user_id": u1.id}

    # Rejected if non-member user
    res = await user_client.post(f"/team/teams/{t3.id}/memberships", json=payload)
    assert res.status_code == 404
    assert await model_count(db, TeamMembership) == 2

    # Rejected if athlete
    res = await user_client.post(f"/team/teams/{t2.id}/memberships", json=payload)
    assert res.status_code == 403
    assert await model_count(db, TeamMembership) == 2

    # Coaches that are not staff should be able to create memberships
    res = await user_client.post(f"/team/teams/{t1.id}/memberships", json=payload)
    assert res.status_code == 201
    assert await model_count(db, TeamMembership) == 3
    await db.refresh(t1)
    assert len(t1.memberships) == 2

    # But non-staff coaches cannot create other coaches
    payload_c = {"user_id": u2.id, "role": TeamRoleType.COACH}
    res = await user_client.post(f"/team/teams/{t1.id}/memberships", json=payload_c)
    assert res.status_code == 403
    assert await model_count(db, TeamMembership) == 3
    await db.refresh(t1)
    assert len(t1.memberships) == 2

    # Staff can create memberships in any team
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post(f"/team/teams/{t3.id}/memberships", json=payload)
    assert res.status_code == 201
    assert await model_count(db, TeamMembership) == 4
    await db.refresh(t3)
    assert len(t3.memberships) == 1

    # Inactive staff cannot create team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["user_id"] = u2.id
    res = await user_client.post(f"/team/teams/{t3.id}/memberships", json=payload)
    assert res.status_code == 401
    assert await model_count(db, TeamMembership) == 4
    await db.refresh(t3)
    assert len(t3.memberships) == 1

    # Admins can create team memberships
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.post(f"/team/teams/{t3.id}/memberships", json=payload)
    assert res.status_code == 201
    assert await model_count(db, TeamMembership) == 5
    await db.refresh(t3)
    assert len(t3.memberships) == 2

    # Inactive admins cannot create team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload["user_id"] = u3.id
    res = await user_client.post(f"/team/teams/{t3.id}/memberships", json=payload)
    assert res.status_code == 401
    assert await model_count(db, TeamMembership) == 5
    await db.refresh(t3)
    assert len(t3.memberships) == 2


async def test_list_team_members_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """Only staff and admins should be able to list team members"""

    t1, t2, t3 = team_memberships_data.get_teams()

    # Listing memberships should return 404 for non-member user
    res = await user_client.get(f"/team/teams/{t3.id}/memberships")
    assert res.status_code == 404

    # Listing memberships should return 403 for athlete
    res = await user_client.get(f"/team/teams/{t2.id}/memberships")
    assert res.status_code == 403

    # Coaches that are not staff should be able to see memberships in their team
    res = await user_client.get(f"/team/teams/{t1.id}/memberships")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == len(t1.memberships)

    # Staff should be able to list memberships from all teams
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == len(t3.memberships)

    # Inactive staff cannot list team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships")
    assert res.status_code == 401

    # Admins can list memberships from any team
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships")
    assert res.status_code == 200

    data = res.json()
    assert len(data) == len(t3.memberships)

    # Inactive admins cannot list team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t1.id}/memberships")
    assert res.status_code == 401


async def test_retrieve_team_members_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """Only staff and admins should be able to get individual team memberships"""

    t1, t2, t3 = team_memberships_data.get_teams()
    tmd = team_memberships_data

    # Athletes can get their own membership
    res = await user_client.get(f"/team/teams/{t2.id}/memberships/{tmd.t2_a1.id}")
    assert res.status_code == 200

    # But athletes cannot get other memberships
    res = await user_client.get(f"/team/teams/{t2.id}/memberships/{tmd.t2_a2.id}")
    assert res.status_code == 403

    # Athletes are forbidden even if membership doesn't exist
    res = await user_client.get(f"/team/teams/{t2.id}/memberships/100")
    assert res.status_code == 403

    # Athletes also can't see memberships on other teams
    res = await user_client.get(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 404

    # Coaches can see memberships on their team
    res = await user_client.get(f"/team/teams/{t1.id}/memberships/{tmd.t1_a1.id}")
    assert res.status_code == 200

    # Staff should be able to see memberships on any team
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 200

    # Inactive staff cannot see anything
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 401

    # Admins can see memberships on any team
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 200

    # Inactive admins cannot see anything
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.get(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 401


async def test_update_team_members_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """Only staff and admins should be able to update teams"""

    t1, _t2, t3 = team_memberships_data.get_teams()
    tmd = team_memberships_data

    payload = {"role": TeamRoleType.COACH}

    # Update should return 404 for regular user (team not found)
    res = await user_client.patch(
        f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}", json=payload
    )
    assert res.status_code == 404

    await db.refresh(tmd.t3_a1)
    assert tmd.t3_a1.role != TeamRoleType.COACH

    # Coaches that are not staff should be rejected with 403
    res = await user_client.patch(
        f"/team/teams/{t1.id}/memberships/{tmd.t1_a1.id}", json=payload
    )
    assert res.status_code == 403

    await db.refresh(tmd.t1_a1)
    assert tmd.t1_a1.role != TeamRoleType.COACH

    # Staff should be able to update team memberships
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(
        f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}", json=payload
    )
    assert res.status_code == 200

    await db.refresh(tmd.t3_a1)
    assert tmd.t3_a1.role == TeamRoleType.COACH

    # Inactive staff cannot update team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"role": TeamRoleType.ATHLETE}
    res = await user_client.patch(
        f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}", json=payload
    )
    assert res.status_code == 401

    await db.refresh(tmd.t3_a1)
    assert tmd.t3_a1.role == TeamRoleType.COACH

    # Admins can update team memberships
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.patch(
        f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}", json=payload
    )
    assert res.status_code == 200

    await db.refresh(tmd.t3_a1)
    assert tmd.t3_a1.role == TeamRoleType.ATHLETE

    # Inactive admins cannot update teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    payload = {"role": TeamRoleType.COACH}
    res = await user_client.patch(
        f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}", json=payload
    )
    assert res.status_code == 401

    await db.refresh(tmd.t3_a1)
    assert tmd.t3_a1.role == TeamRoleType.ATHLETE


async def test_delete_team_members_perms(
    db: AsyncSession,
    user_client: AsyncClient,
    current_user: User,
    team_memberships_data: TeamMembershipsData,
):
    """Staff, admins, and coaches should be able to delete team members"""

    t1, t2, t3 = team_memberships_data.get_teams()
    tmd = team_memberships_data

    # Non-members shouldn't be able to delete a membership (team not found)
    res = await user_client.delete(f"/team/teams/{t3.id}/memberships/{tmd.t3_a1.id}")
    assert res.status_code == 404

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t3_a1.id))
        == 1
    )

    # Athlets shoudln't be able to delete a membership
    res = await user_client.delete(f"/team/teams/{t2.id}/memberships/{tmd.t2_a2.id}")
    assert res.status_code == 403

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t2_a2.id))
        == 1
    )

    # Coaches should be able to delete an athlete
    res = await user_client.delete(f"/team/teams/{t1.id}/memberships/{tmd.t1_a1.id}")
    assert res.status_code == 200

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t1_a1.id))
        == 0
    )

    # Non-staff coaches should not be able to delete another coach
    res = await user_client.delete(f"/team/teams/{t1.id}/memberships/{tmd.t1_c2.id}")
    assert res.status_code == 403

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t1_c2.id))
        == 1
    )

    # Staff should be able to delete any team memberships
    current_user.is_staff = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t3.id}/memberships/{tmd.t3_c1.id}")
    assert res.status_code == 200

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t3_c1.id))
        == 0
    )

    # Inactive staff cannot delete any team memberships
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t3.id}/memberships/{tmd.t3_c2.id}")
    assert res.status_code == 401

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t3_c2.id))
        == 1
    )

    # Admins can delete any team memberships
    current_user.is_staff = False
    current_user.is_admin = True
    current_user.is_active = True
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t3.id}/memberships/{tmd.t3_c2.id}")
    assert res.status_code == 200

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t3_c2.id))
        == 0
    )

    # Inactive admins cannot delete teams
    current_user.is_active = False
    db.add(current_user)
    await db.commit()

    res = await user_client.delete(f"/team/teams/{t3.id}/memberships/{tmd.t3_c3.id}")
    assert res.status_code == 401

    assert (
        await model_count(db, TeamMembership, where=(TeamMembership.id == tmd.t3_c3.id))
        == 1
    )
