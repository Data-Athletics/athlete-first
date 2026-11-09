from typing import Annotated

from fastapi import HTTPException, Path, status
from pydantic import SecretStr
from sqlalchemy import and_, exists, select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import CurrentUserDep
from app.auth.services import get_password_hash
from app.core.dependencies import AsyncSessionDep
from app.team.models import Team, TeamMembership, TeamRoleType
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
                    )
                )
            ),
            # Target user has a membership
            exists(
                select(TeamMembership.id).where(
                    and_(
                        TeamMembership.team_id == Team.id,
                        TeamMembership.user_id == user_id,
                    )
                )
            ),
        )
    )
    rows = await db.execute(query)
    matched_team_ids = list(rows.scalars())
    can_access = len(matched_team_ids) > 0

    # If not, return a plain 404 error
    if not can_access and not current_user.is_admin:
        raise not_found_error
    elif current_user.is_admin:
        print("Allowing admin")
    else:
        print("Matching teams:", matched_team_ids)

    # Finally, safely check if the user exists
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if user is None and can_access is True:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A team membership exists for a user that does not exist",
        )
    elif user is None:
        raise not_found_error

    return user


async def create_user(
    db: AsyncSessionDep, username: str, password: SecretStr | str | None, **kwargs
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
