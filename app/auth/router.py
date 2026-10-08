from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status

from app.auth.dtos import OAuthRequestDTO
from app.auth.dtos.oauth_dto import OAuthResponseDTO
from app.auth.dtos.register_dto import RegisterUserDTO
from app.auth.services import authenticate_user, get_user_token
from app.core.dependencies import AsyncSessionDep
from app.user.dtos.user_dto import UserDTO
from app.user.services import create_user

router = APIRouter()


@router.post("/token", response_model=OAuthResponseDTO)
async def login_user_route(
    db: AsyncSessionDep, body: Annotated[OAuthRequestDTO, Form()]
):
    """Authenticate user with their username/password"""

    # Retrieve the user from credentials
    user = await authenticate_user(db, username=body.username, password=body.password)
    if not user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
        )

    # Create and return the JWT access token
    access_token = get_user_token(user)
    return OAuthResponseDTO(access_token=access_token.encode())


@router.post("/register", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
async def register_user_route(db: AsyncSessionDep, body: RegisterUserDTO):
    """Allow user to create their own account"""

    data = body.model_dump()
    return await create_user(db, **data)


__all__ = ["router"]
