from typing import Annotated

from fastapi import Depends

from app.user.models import User
from app.user.services import get_user_by_id

UserByIdDep = Annotated[User, Depends(get_user_by_id)]
"""
Retrieve a single user by it's id in the url path,
or raise a 404 error if it's not found.
"""
