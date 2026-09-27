from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status

from app.auth.dtos import OAuthRequestDTO
from app.auth.dtos.oauth_dto import OAuthResponseDTO
from app.auth.services import authenticate_user, get_user_token
from app.core.dependencies import AsyncSessionDep

router = APIRouter()


@router.post("/token")
async def login_user_route(
    db: AsyncSessionDep, body: Annotated[OAuthRequestDTO, Form()]
) -> OAuthResponseDTO:
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


__all__ = ["router"]
