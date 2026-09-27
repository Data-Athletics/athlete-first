from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from app.auth.config import oauth2_scheme
from app.auth.dtos.token_dto import TokenClaimsDTO
from app.core.dependencies import AsyncSessionDep
from app.user.models import User


async def get_current_user(
    db: AsyncSessionDep, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Get the current user from their access token"""

    # Get and verify the token's claims
    claims = TokenClaimsDTO.decode(token)
    if claims.is_expired:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token is expired")

    # Get the user associated with the token
    rows = await db.execute(select(User).where(User.id == int(claims.sub)))
    user = rows.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unable to authenticate user")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
"""Get the currently authenticated user"""
