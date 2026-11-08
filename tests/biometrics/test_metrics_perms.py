from dataclasses import dataclass

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.biometrics.dtos.MetricsDTOs import BOOL_METRICS, BoolMetricType
from app.core.dtos import PermissionDeniedReason
from app.team.models import MembershipDsp, Team, TeamDsr, TeamMembership, TeamRoleType
from app.user.models import User
from tests.auth.utils import create_test_user_token
from tests.team.utils import create_test_team
from tests.user.utils import create_test_users


@dataclass
class MetricsAccessData:
    """Mock team data with varying levels of access permission"""

    # Teams
    team1: Team
    team2: Team
    team3: Team

    # DSRs
    dsr1: TeamDsr
    dsr2: TeamDsr
    dsr3: TeamDsr

    # Users
    cu: User
    """Alias for `current_user`"""

    u1: User
    u2: User
    u3: User
    u4: User
    u5: User

    # Memberships & DSPs
    cu_mem1: TeamMembership
    """Coach"""
    cu_mem2: TeamMembership
    """Coach"""

    cu_mem3: TeamMembership
    """Athlete"""

    @property
    def cu_dsp3(self) -> MembershipDsp:
        assert self.cu_mem3.dsp is not None
        return self.cu_mem3.dsp

    u1_mem1: TeamMembership
    """Athlete"""

    @property
    def u1_dsp1(self) -> MembershipDsp:
        assert self.u1_mem1.dsp is not None
        return self.u1_mem1.dsp

    u1_mem2: TeamMembership
    """Athlete"""

    @property
    def u1_dsp2(self) -> MembershipDsp:
        assert self.u1_mem2.dsp is not None
        return self.u1_mem2.dsp

    u2_mem1: TeamMembership
    """Athlete"""

    @property
    def u2_dsp1(self) -> MembershipDsp:
        assert self.u2_mem1.dsp is not None
        return self.u2_mem1.dsp

    u3_mem2: TeamMembership
    """Athlete"""

    @property
    def u3_dsp2(self) -> MembershipDsp:
        assert self.u3_mem2.dsp is not None
        return self.u3_mem2.dsp

    u4_mem3: TeamMembership
    """Coach"""

    @property
    def u4_dsp3(self) -> MembershipDsp:
        assert self.u4_mem3.dsp is not None
        return self.u4_mem3.dsp

    u5_mem3: TeamMembership
    """Athlete"""

    @property
    def u5_dsp3(self) -> MembershipDsp:
        assert self.u5_mem3.dsp is not None
        return self.u5_mem3.dsp


@pytest.fixture(scope="function", name="metrics_access_data")
async def setup_metrics_access_data(db: AsyncSession, current_user: User):
    """Setup team data for data access"""

    # Users
    u1, u2, u3, u4, u5 = await create_test_users(db, count=5)

    # Teams
    team1 = await create_test_team(
        db, create_dsps=True, create_dsr=True, user_ids=[current_user.id, u1.id, u2.id]
    )
    team2 = await create_test_team(
        db, create_dsps=True, create_dsr=True, user_ids=[current_user.id, u1.id, u3.id]
    )
    team3 = await create_test_team(
        db, create_dsps=True, create_dsr=True, user_ids=[current_user.id, u4.id, u5.id]
    )

    assert team1.dsr is not None
    assert team2.dsr is not None
    assert team3.dsr is not None

    # Combine test data
    data = MetricsAccessData(
        team1=team1,
        team2=team2,
        team3=team3,
        dsr1=team1.dsr,
        dsr2=team2.dsr,
        dsr3=team3.dsr,
        cu=current_user,
        u1=u1,
        u2=u2,
        u3=u3,
        u4=u4,
        u5=u5,
        cu_mem1=next(m for m in team1.memberships if m.user_id == current_user.id),
        cu_mem2=next(m for m in team2.memberships if m.user_id == current_user.id),
        cu_mem3=next(m for m in team3.memberships if m.user_id == current_user.id),
        u1_mem1=next(m for m in team1.memberships if m.user_id == u1.id),
        u1_mem2=next(m for m in team2.memberships if m.user_id == u1.id),
        u2_mem1=next(m for m in team1.memberships if m.user_id == u2.id),
        u3_mem2=next(m for m in team2.memberships if m.user_id == u3.id),
        u4_mem3=next(m for m in team3.memberships if m.user_id == u4.id),
        u5_mem3=next(m for m in team3.memberships if m.user_id == u5.id),
    )

    # Make current user a coach of team 1 & 2, but not 3
    data.cu_mem1.role = TeamRoleType.COACH
    data.cu_mem2.role = TeamRoleType.COACH

    # Make u4 the coach of team 3
    data.u4_mem3.role = TeamRoleType.COACH

    db.add_all([data.cu_mem1, data.cu_mem2, data.u4_mem3])
    await db.commit()

    return data


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_admin_access_metrics(
    metric: BoolMetricType,
    admin_client: AsyncClient,
    metrics_access_data: MetricsAccessData,
):
    """Admins should be able to access all metrics"""

    metric_slug = metric.replace("_", "-")

    res = await admin_client.get(
        f"/biometrics/{metrics_access_data.u1.id}/{metric_slug}"
    )
    assert res.status_code == 200

    res = await admin_client.get(
        f"/biometrics/{metrics_access_data.u2.id}/{metric_slug}"
    )
    assert res.status_code == 200

    res = await admin_client.get(
        f"/biometrics/{metrics_access_data.u3.id}/{metric_slug}"
    )
    assert res.status_code == 200

    res = await admin_client.get(
        f"/biometrics/{metrics_access_data.u5.id}/{metric_slug}"
    )
    assert res.status_code == 200


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_member_access_metrics(
    metric: BoolMetricType,
    user_client: AsyncClient,
    current_user: User,
    metrics_access_data: MetricsAccessData,
):
    """Basic team members should only be able to see their own data"""

    metric_slug = metric.replace("_", "-")

    # Should view own data
    res = await user_client.get(f"/biometrics/{current_user.id}/{metric_slug}")
    assert res.status_code == 200, res.content

    # Should not view other's data (returns 404 since user shouldn't be able to list users)
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u4.id}/{metric_slug}"
    )
    assert res.status_code == 404


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_dsp_bool_metrics_access(
    metric: BoolMetricType,
    db: AsyncSession,
    user_client: AsyncClient,
    metrics_access_data: MetricsAccessData,
):
    """A user's data sharing policy should effect metrics access"""

    policy = f"{metric}_shared"
    metric_slug = metric.replace("_", "-")
    print("metric slug:", metric_slug)

    # Based on default policies, coach should be able to view the data
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u1.id}/{metric_slug}"
    )
    assert res.status_code == 200

    # User 1 restricts bpm but not calories for team1
    metrics_access_data.u1_dsp1.content = {policy: False}
    db.add(metrics_access_data.u1_dsp1)
    await db.commit()

    # Based on default policies of team2, coach should still be able to view the data
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u1.id}/{metric_slug}"
    )
    assert res.status_code == 200

    # User 1 restricts bpm but not calories for team2
    metrics_access_data.u1_dsp2.content = {policy: False}
    db.add(metrics_access_data.u1_dsp2)
    await db.commit()

    # Coach no longer can see the bpm
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u1.id}/{metric_slug}"
    )
    assert res.status_code == 403
    data = res.json()
    print('data:', data)
    assert res.json()["reason"] == PermissionDeniedReason.POLICY_RESTRICTION

    # Coach can still see other metrics
    if metric != "calories":
        res = await user_client.get(f"/biometrics/{metrics_access_data.u1.id}/calories")
        assert res.status_code == 200
    else:
        res = await user_client.get(f"/biometrics/{metrics_access_data.u1.id}/bpm")
        assert res.status_code == 200

    # Coach can also still see bpm from another user
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u2.id}/{metric_slug}"
    )
    assert res.status_code == 200


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_dsr_metrics_access(
    metric: BoolMetricType,
    db: AsyncSession,
    user_client: AsyncClient,
    metrics_access_data: MetricsAccessData,
):
    """A team's data sharing requirements should effect default metrics access"""

    policy = f"{metric}_shared"
    metric_slug = metric.replace("_", "-")

    # The team1 policy restricts calorie sharing
    metrics_access_data.dsr1.content = {policy: False}
    db.add(metrics_access_data.dsr1)
    await db.commit()

    # Coach can still see calories for u1 due to team2 defaults
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u1.id}/{metric_slug}"
    )
    assert res.status_code == 200

    # Coach cannot see calories for u2
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.u2.id}/{metric_slug}"
    )
    assert res.status_code == 403
    assert res.json()["reason"] == PermissionDeniedReason.POLICY_RESTRICTION

    # Coach can still see other metrics
    if metric != "calories":
        res = await user_client.get(f"/biometrics/{metrics_access_data.u1.id}/calories")
        assert res.status_code == 200
    else:
        res = await user_client.get(f"/biometrics/{metrics_access_data.u1.id}/bpm")
        assert res.status_code == 200


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_null_dsp_access(
    metric: BoolMetricType,
    db: AsyncSession,
    user_client: AsyncClient,
    metrics_access_data: MetricsAccessData,
):
    """User shouldn't be able to see data if dsp is null"""

    metric_slug = metric.replace("_", "-")

    # DSP set to null, simulates user just joined the team
    await db.delete(metrics_access_data.cu_mem3.dsp)
    await db.commit()
    await db.refresh(metrics_access_data.cu_mem3)
    assert metrics_access_data.cu_mem3.dsp is None

    # If any of the user's memberships don't have a dsp, disallow viewing their own metrics
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.cu.id}/{metric_slug}"
    )
    assert res.status_code == 403
    assert res.json()["reason"] == PermissionDeniedReason.NULL_POLICY


@pytest.mark.parametrize("metric", BOOL_METRICS)
async def test_invalid_dsp_by_dsr(
    metric: BoolMetricType,
    db: AsyncSession,
    client: AsyncClient,
    user_client: AsyncClient,
    metrics_access_data: MetricsAccessData,
):
    """User shouldn't be able to see their data if their dsp is not aligned with the team's dsr"""

    policy = f"{metric}_shared"
    metric_slug = metric.replace("_", "-")

    # Team 3 requires metric
    metrics_access_data.dsr3.content = {policy: True}
    db.add(metrics_access_data.dsr3)
    await db.commit()

    # But current user has their policy restrict it
    metrics_access_data.cu_dsp3.content = {policy: False}
    db.add(metrics_access_data.cu_dsp3)
    await db.commit()

    # When the user tries to see their own data (this metric and others), reject it
    res = await user_client.get(
        f"/biometrics/{metrics_access_data.cu.id}/{metric_slug}"
    )
    assert res.status_code == 403
    assert res.json()["reason"] == PermissionDeniedReason.INVALID_POLICY

    if metric != "calories":
        res = await user_client.get(f"/biometrics/{metrics_access_data.cu.id}/calories")
        assert res.status_code == 403
        assert res.json()["reason"] == PermissionDeniedReason.INVALID_POLICY
    else:
        res = await user_client.get(f"/biometrics/{metrics_access_data.cu.id}/bpm")
        assert res.status_code == 403
        assert res.json()["reason"] == PermissionDeniedReason.INVALID_POLICY

    # The coach should not be able to see this metric
    u4_token = create_test_user_token(metrics_access_data.u4)
    res = await client.get(
        f"/biometrics/{metrics_access_data.cu.id}/{metric_slug}",
        headers={"Authorization": f"Bearer {u4_token}"},
    )
    assert res.status_code == 403
    assert res.json()["reason"] == PermissionDeniedReason.POLICY_RESTRICTION

    # But the coach should be able to see other metrics
    if metric != "calories":
        res = await client.get(
            f"/biometrics/{metrics_access_data.cu.id}/calories",
            headers={"Authorization": f"Bearer {u4_token}"},
        )
        assert res.status_code == 200
    else:
        res = await client.get(
            f"/biometrics/{metrics_access_data.cu.id}/bpm",
            headers={"Authorization": f"Bearer {u4_token}"},
        )
        assert res.status_code == 200
