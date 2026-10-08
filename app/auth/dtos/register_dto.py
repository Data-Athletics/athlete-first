from pydantic import Field, SecretStr

from app.core.dtos import BaseDTO


class RegisterUserDTO(BaseDTO):
    """Fields needed for a new user to register themselves"""

    username: str = Field(min_length=5)
    password: SecretStr = Field(min_length=6)
