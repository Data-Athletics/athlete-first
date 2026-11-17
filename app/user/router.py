from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import CurrentUserDep, get_current_user
from app.auth.services import get_password_hash
from app.core.dependencies import AsyncSessionDep
from app.team.dependencies import current_user_is_any_coach_dep
from app.user.dependencies import UserByIdDep, current_user_is_staff_dep
from app.user.dtos.user_dto import CreateUserDTO, UpdateMeDTO, UpdateUserDTO, UserDTO
from app.user.services import create_user, list_users

router = APIRouter(dependencies=[Depends(get_current_user)])


# -------------------------------
# Users CRUD Routes
# -------------------------------

users_router = APIRouter(prefix="/users")
users_staff_router = APIRouter(
    prefix="/users", dependencies=[Depends(current_user_is_staff_dep)]
)


@users_router.get(
    "",
    response_model=list[UserDTO],
    dependencies=[Depends(current_user_is_any_coach_dep)],
)
async def list_users_route(db: AsyncSessionDep, current_user: CurrentUserDep):
    """Get a list of users from the database"""

    return await list_users(db, current_user=current_user)


@users_staff_router.post(
    "", response_model=UserDTO, status_code=status.HTTP_201_CREATED
)
async def create_user_route(db: AsyncSessionDep, body: CreateUserDTO):
    """Create a new user"""

    data = body.model_dump()
    return await create_user(db, **data)


@users_router.get(
    "/{user_id}",
    response_model=UserDTO,
    dependencies=[Depends(current_user_is_any_coach_dep)],
)
async def retrieve_user_route(user: UserByIdDep):
    """Get a single user by their id"""

    return user


@users_staff_router.patch("/{user_id}", response_model=UserDTO)
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


@users_staff_router.delete("/{user_id}", response_model=UserDTO)
async def delete_user_route(db: AsyncSessionDep, user: UserByIdDep):
    """Delete user by id"""

    await db.delete(user)
    await db.flush()

    return user


router.include_router(users_router)
router.include_router(users_staff_router)

# -------------------------------
# Current User (me) Routes
# -------------------------------

me_router = APIRouter(prefix="/me")


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
