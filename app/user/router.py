from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import AsyncSessionDep
from app.user.dependencies import UserByIdDep
from app.user.dtos.user_dto import CreateUserDTO, UpdateUserDTO, UserDTO
from app.user.models import User

router = APIRouter()


# -------------------------------
# Users CRUD Routes
# -------------------------------

users_router = APIRouter(prefix="/users")


@users_router.get("", response_model=list[UserDTO])
async def list_users_route(db: AsyncSessionDep):
    """Get a list of users from the database"""

    res = await db.execute(select(User))
    return res.scalars().all()


@users_router.post("", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
async def create_user_route(db: AsyncSessionDep, body: CreateUserDTO):
    """Create a new user"""

    user = User(**body.model_dump())
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

me_router = APIRouter(prefix="/me")


@me_router.get("", response_model=UserDTO)
async def retrieve_my_info(db: AsyncSessionDep):
    """Get information for the currently logged in user"""

    raise NotImplementedError()


@me_router.patch("", response_model=UserDTO)
async def update_my_info(db: AsyncSessionDep):
    """Partially update info for the current user"""

    raise NotImplementedError()


router.include_router(me_router)


__all__ = ["router"]
