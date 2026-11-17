from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import CurrentUserDep
from app.core.exceptions import PermissionException
from app.user.models import User
from app.user.services import get_user_by_id

UserByIdDep = Annotated[User, Depends(get_user_by_id)]
"""
Retrieve a single user by it's id in the url path,
or raise a 404 error if it's not found.
"""


async def current_user_is_staff_dep(user: CurrentUserDep):
    """Only return if the user is staff or admin"""

    if not user.is_staff and not user.is_admin:
        raise PermissionException(
            detail="User needs to be staff or admin to access this"
        )

    return True
