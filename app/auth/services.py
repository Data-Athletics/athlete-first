from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dtos import TokenClaimsDTO
from app.user.models import User

password_hasher = PasswordHash((Argon2Hasher(),))
"""
Password hash generator using the Argon2 algorithm,
ref: https://en.wikipedia.org/wiki/Argon2
"""


def get_password_hash(plain_password: str) -> str:
    """
    Get a hash value (with random salt) for a plain password that can be stored
    """

    return password_hasher.hash(plain_password)


def verify_password_hash(plain_password: str, password_hash: str) -> bool:
    """Compare a plain password to a target password hash to see if the password is correct"""

    return password_hasher.verify(plain_password, password_hash)


async def authenticate_user(
    db: AsyncSession, username: str, password: SecretStr | str
) -> User | None:
    """Get a user that matches the username and password"""

    # Search for user with the username
    rows = await db.execute(select(User).where(User.username == username))
    user = rows.scalar_one_or_none()

    # Return None if the's no user or the user doesn't have a password
    if user is None or user.hashed_password is None:
        return None

    # Extract the raw password
    if isinstance(password, SecretStr):
        raw_password = password.get_secret_value()
    else:
        raw_password = password

    # Return None if the passwords don't match
    if not verify_password_hash(raw_password, user.hashed_password):
        return None

    return user


def get_user_token(user: User) -> TokenClaimsDTO:
    """Get the JWT token claims object for a user"""

    return TokenClaimsDTO(sub=str(user.id))
