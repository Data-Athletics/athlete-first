from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.services import get_password_hash
from app.core.faker import fake
from app.team.models import Team, TeamMembership, TeamRoleType
from app.user.models import User
from tests.team.utils import create_test_team_membership


@dataclass
class UserPermsData:
    """Provides mock data for various levels of user roles"""

    u1: User
    """Basic user"""

    s1: User
    """Staff user"""

    a1: User
    """Admin user"""

    t1: Team
    """Team with a coach and athlete"""

    tc1: User
    """Coach for team 1"""

    ta1: User
    """Athlete for team 1"""

    async def _set_is_active(self, db: AsyncSession, user: User, is_active=True):
        """Set user as inactive"""

        user.is_active = is_active
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    async def set_active(self, db: AsyncSession, user: User):
        """Set user as active"""

        return await self._set_is_active(db, user, is_active=True)

    async def set_inactive(self, db: AsyncSession, user: User):
        """Set user as inactive"""

        return await self._set_is_active(db, user, is_active=False)

    async def set_user(self, db: AsyncSession, user: User):
        """Set user as a normal non-staff non-admin user"""

        user.is_staff = False
        user.is_admin = False
        user.is_active = True
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    async def set_staff(self, db: AsyncSession, user: User, is_active=True):
        """Set user as a staff user"""

        user.is_staff = True
        user.is_admin = False
        user.is_active = is_active
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    async def set_admin(self, db: AsyncSession, user: User, is_active=True):
        """Set user as a admin user"""

        user.is_staff = False
        user.is_admin = True
        user.is_active = is_active
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    async def set_coach(self, db: AsyncSession, user: User) -> TeamMembership:
        """Set the provided user as a coach of team 1"""

        membership = next(
            (mem for mem in self.t1.memberships if mem.user_id == user.id), None
        )

        if membership is None:
            return await create_test_team_membership(
                db, user_id=user.id, team_id=self.t1.id, is_coach=True
            )
        else:
            membership.role = TeamRoleType.COACH
            db.add(membership)
            await db.commit()
            await db.refresh(membership)
            return membership

    async def remove_from_team(self, db: AsyncSession, user: User) -> bool:
        """Remove the user from team 1 (if applicable), returns true if was a member of the team"""

        membership = next(
            (mem for mem in self.t1.memberships if mem.user_id == user.id), None
        )

        if membership is None:
            return False
        else:
            await db.delete(membership)
            await db.commit()
            return True


def base_user_payload():
    """Creates a base user payload for testing convenience"""

    return {
        "username": fake.username(),
        "name": fake.name(),
        "height": fake.height(),
        "weight": fake.weight(),
        "sex": fake.sex(),
        "age": fake.age(),
    }


async def create_test_user(db: Optional[AsyncSession] = None, **kwargs):
    """Create mock user for testing"""

    password = kwargs.pop("password", None)
    payload = {**base_user_payload(), **kwargs}

    if password:
        payload["hashed_password"] = get_password_hash(password)

    user = User(**payload)

    if db:
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def create_test_users(db: Optional[AsyncSession] = None, count=5, **kwargs):
    """Create multiple test users"""

    users: list[User] = [await create_test_user(**kwargs) for _ in range(count)]

    # If there's a database, commit them all at once
    if db:
        db.add_all(users)
        await db.commit()

        for user in users:
            await db.refresh(user)

    return users
