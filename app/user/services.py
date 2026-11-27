from typing import Annotated

from fastapi import HTTPException, Path, status
from pydantic import SecretStr
from sqlalchemy import and_, desc, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUserDep
from app.auth.services import get_password_hash
from app.core.dependencies import AsyncSessionDep
from app.core.dtos import PermissionDeniedReason
from app.core.exceptions import PermissionException
from app.team.models import Team, TeamMembership, TeamMembershipStatusType, TeamRoleType
from app.user.models import User


async def get_user_by_id(
    db: AsyncSessionDep, current_user: CurrentUserDep, user_id: Annotated[int, Path()]
) -> User:
    """Retrieve user by id or raise 404"""

    not_found_error = HTTPException(
        status.HTTP_404_NOT_FOUND, detail=f"User not found for id {user_id}"
    )

    # First, if target user is the current one, just return the current user
    if current_user.id == user_id:
        return current_user

    if current_user.is_admin or current_user.is_staff:
        can_access = True
    else:
        # Otherwise, check if there is a context under which the current user can see this user
        query = select(Team.id).where(
            and_(
                # Current user is coach
                exists(
                    select(TeamMembership.id).where(
                        and_(
                            TeamMembership.team_id == Team.id,
                            TeamMembership.user_id == current_user.id,
                            TeamMembership.role == TeamRoleType.COACH,
                            TeamMembership.status == TeamMembershipStatusType.APPROVED,
                        )
                    )
                ),
                # Target user has a membership
                exists(
                    select(TeamMembership.id).where(
                        and_(
                            TeamMembership.team_id == Team.id,
                            TeamMembership.user_id == user_id,
                            TeamMembership.status == TeamMembershipStatusType.APPROVED,
                        )
                    )
                ),
            )
        )
        rows = await db.execute(query)
        matched_team_ids = list(rows.scalars())
        can_access = len(matched_team_ids) > 0

    # If not, return a plain 404 error
    if not can_access:
        raise not_found_error

    # Finally, safely retrieve the user
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if user is None:
        raise not_found_error

    return user


async def create_user(
    db: AsyncSession, username: str, password: SecretStr | str | None, **kwargs
) -> User:
    """Create a new user and set their password"""

    # Extract and hash password
    if isinstance(password, SecretStr):
        password = password.get_secret_value()

    if password is not None:
        kwargs["hashed_password"] = get_password_hash(password)

    # Set user fields
    user = User(username=username, **kwargs)
    db.add(user)

    # Try to save changes, raise 400 if there's a unique violation
    try:
        await db.flush()
        await db.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        ) from e

    return user


async def list_users(db: AsyncSession, current_user: User):
    """List users available to the current user"""

    query = select(User).order_by(desc(User.created_at))

    if not current_user.is_admin and not current_user.is_staff:
        team_ids = list({mem.team_id for mem in current_user.memberships})
        query = query.where(User.memberships.any(TeamMembership.team_id.in_(team_ids)))

    res = await db.execute(query)
    return res.scalars().all()


def require_staff_user(
    user: User, message="User needs to be staff or admin to access this"
):
    """Raise 403 forbidden error if the user is not staff"""

    if not user.is_staff and not user.is_admin:
        raise PermissionException(
            detail=message, reason=PermissionDeniedReason.STAFF_ONLY
        )

    return True


def require_admin_user(user: User, message="User needs to be an admin to access this"):
    """Raise 403 forbidden error if the user is not staff"""

    if not user.is_admin:
        raise PermissionException(
            detail=message, reason=PermissionDeniedReason.ADMINS_ONLY
        )

    return True
