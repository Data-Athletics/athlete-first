from typing import Literal

from pydantic import Field, SecretStr
from pydantic.json_schema import SkipJsonSchema

from app.auth.config import auth_settings
from app.core.dtos import BaseDTO


class OAuthRequestDTO(BaseDTO):
    """Fields used to log in a user

    Ref: [RFC6749 Section 4.3.2](https://www.rfc-editor.org/info/rfc6749/#section-4.3.2)
    """

    username: str = Field(description="The resource owner username")
    password: SecretStr = Field(description="The resource owner password")
    grant_type: Literal["password"] = Field(
        description="Used to determine what type of OAuth2.0 flow to use",
        default="password",
    )

    # Fields allowed under OAuth2.0 spec, but are not used here
    client_id: SkipJsonSchema[str] | None = None
    client_secret: SkipJsonSchema[str] | None = None


class OAuthResponseDTO(BaseDTO):
    """Tokens returned from a login request

    Ref: [RFC6749 Section 5.1](https://www.rfc-editor.org/info/rfc6749/#section-5.1)
    """

    access_token: str = Field(
        description="Authentication bearer token to use for authenticated API requests"
    )
    token_type: Literal["bearer"] = Field(
        description="The type of OAuth2.0 access token being provided, see [RFC6749 Section 7.1](https://www.rfc-editor.org/info/rfc6749/#section-7.1)",
        default="bearer",
    )
    expires_in: int = Field(
        description="Number of seconds the token is valid for",
        default=auth_settings.jwt_ttl_seconds,
    )
