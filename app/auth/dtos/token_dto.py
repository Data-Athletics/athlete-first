from datetime import UTC, datetime

import jwt
from pydantic import Field

from app.auth.config import auth_settings
from app.core.dtos import BaseDTO


class TokenClaimsDTO(BaseDTO):
    """JWT token claims

    Ref: [RFC7519 Section 4](https://www.rfc-editor.org/info/rfc7519/#section-4)
    """

    sub: str = Field(description="Claims subject, in this case it's the user id")
    iat: int = Field(
        description="Claims issued at time, number of seconds from the epoch",
        default_factory=lambda: int(datetime.now(UTC).timestamp()),
    )
    exp: int = Field(
        description="Claims expiration time, number of seconds from the epoch",
        default_factory=lambda: int(
            (datetime.now(UTC) + auth_settings.jwt_ttl_timedelta).timestamp()
        ),
    )

    @property
    def is_expired(self):
        """Returns true if the expiration time is less than the current time"""

        return self.exp < datetime.now().timestamp()

    def encode(self) -> str:
        """Encode token claims into an encrypted JWT token"""

        return jwt.encode(
            self.model_dump(),
            auth_settings.jwt_secret_key,
            algorithm=auth_settings.jwt_algorithm,
        )

    @classmethod
    def decode(cls, token: str) -> "TokenClaimsDTO":
        """Decode a token and return the claims"""

        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
        )
        return cls(**payload)
