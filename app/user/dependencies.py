from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import CurrentUserDep
from app.user.models import User
from app.user.services import get_user_by_id, require_admin_user, require_staff_user

UserByIdDep = Annotated[User, Depends(get_user_by_id)]
"""
Retrieve a single user by it's id in the url path,
or raise a 404 error if it's not found.
"""


async def current_user_is_staff_dep(user: CurrentUserDep):
    """Only return if the user is staff or admin"""

    return require_staff_user(user)


async def current_user_is_admin_dep(user: CurrentUserDep):
    """Only return if the user is admin"""

    return require_admin_user(user)
