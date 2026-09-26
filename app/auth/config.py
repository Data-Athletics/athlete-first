from datetime import timedelta

from fastapi.security import OAuth2PasswordBearer
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from app.core.config import app_settings


class AuthSettings(BaseSettings):
    """General config for the authentication service"""

    jwt_secret_key: str = Field(
        description="Key used to encrypt JWT tokens", default="insecure-changeme123456789abcdef"
    )
    jwt_algorithm: str = Field(
        description="The algorithm used to encrypt JWT tokens", default="HS256"
    )
    jwt_ttl_seconds: int = Field(
        description="JWT token's time to live, number of seconds until the token expires",
        default=timedelta(hours=1).seconds,
    )

    @field_validator("jwt_secret_key", mode="after")
    @classmethod
    def prevent_insecure_jwt_secret(cls, key: str):
        """Prevent insecure secret keys from being used in prod"""

        if app_settings.env != "prod":
            return key

        # Ensure the key is strong enough
        if key.startswith("insecure-"):
            raise ValueError("Cannot use insecure JWT secret in production!")
        elif len(key) < 32:
            raise ValueError("JWT secret must be larger than or equal to 32 characters")

        return key

    @property
    def jwt_ttl_timedelta(self):
        return timedelta(seconds=self.jwt_ttl_seconds)


auth_settings = AuthSettings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

__all__ = ["auth_settings", "oauth2_scheme"]
