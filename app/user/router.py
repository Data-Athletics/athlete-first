from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from pydantic import SecretStr
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import CurrentUserDep, get_current_user
from app.auth.services import get_password_hash
from app.core.dependencies import AsyncSessionDep
from app.user.dependencies import UserByIdDep
from app.user.dtos.user_dto import CreateUserDTO, UpdateMeDTO, UpdateUserDTO, UserDTO
from app.user.models import User

router = APIRouter()

# -------------------------------
# Users Public Routes
# -------------------------------

public_users_router = APIRouter(prefix="/users")


@public_users_router.post(
    "", response_model=UserDTO, status_code=status.HTTP_201_CREATED
)
async def create_user_route(db: AsyncSessionDep, body: CreateUserDTO):
    """Create a new user"""

    data = body.model_dump()
    password_entry: SecretStr | None = data.pop("password", None)

    if password_entry is not None:
        password = password_entry.get_secret_value()
        data["hashed_password"] = get_password_hash(password)

    user = User(**data)
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


router.include_router(public_users_router)

# -------------------------------
# Users CRUD Routes
# -------------------------------

users_router = APIRouter(prefix="/users", dependencies=[Depends(get_current_user)])


@users_router.get("", response_model=list[UserDTO])
async def list_users_route(db: AsyncSessionDep):
    """Get a list of users from the database"""

    res = await db.execute(select(User).order_by(desc(User.created_at)))
    return res.scalars().all()


@users_router.get("/{user_id}", response_model=UserDTO)
async def retrieve_user_route(user: UserByIdDep):
    """Get a single user by their id"""

    return user


@users_router.patch("/{user_id}", response_model=UserDTO)
async def update_user_route(
    db: AsyncSessionDep, user: UserByIdDep, body: UpdateUserDTO
):
    """Partially update a user"""

    data = body.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(user, key, value)

    db.add(user)

    try:
        await db.flush()
        await db.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists with the new values",
        ) from e

    return user


@users_router.delete("/{user_id}", response_model=UserDTO)
async def delete_user_route(db: AsyncSessionDep, user: UserByIdDep):
    """Delete user by id"""

    await db.delete(user)
    await db.flush()

    return user


router.include_router(users_router)

# -------------------------------
# Current User (me) Routes
# -------------------------------

me_router = APIRouter(prefix="/me", dependencies=[Depends(get_current_user)])


@me_router.get("", response_model=UserDTO)
async def retrieve_my_info(user: CurrentUserDep):
    """Get information for the currently logged in user"""

    return user


@me_router.patch("", response_model=UserDTO)
async def update_my_info(db: AsyncSessionDep, user: CurrentUserDep, body: UpdateMeDTO):
    """Partially update info for the current user"""

    data = body.model_dump(exclude_unset=True)
    password_entry: SecretStr | None = data.pop("password", None)

    if password_entry is not None:
        password = password_entry.get_secret_value()
        data["hashed_password"] = get_password_hash(password)

    for key, value in data.items():
        setattr(user, key, value)

    db.add(user)

    try:
        await db.flush()
        await db.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists with the new values",
        ) from e

    return user


router.include_router(me_router)


__all__ = ["router"]
