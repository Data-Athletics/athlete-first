from pydantic import Field

from app.core.dtos import BaseDTO, BaseModelDTO


class BaseUserDTO(BaseDTO):
    """Base fields for user api"""

    username: str = Field(description="Unique username")
    is_active: bool = Field(
        description="Determines whether the user can login, and whether their metrics are counted in grouped aggregations",
        default=True,
    )


class UserDTO(BaseModelDTO, BaseUserDTO):
    """Fields provided in the API for an application user"""

    id: int = Field(description="Primary key")
    can_login: bool = Field(description="Whether they have a usable password or not")


class CreateUserDTO(BaseUserDTO):
    """Fields needed to create a new user"""

    pass


class UpdateUserDTO(BaseUserDTO):
    """Fields available to update for a user"""

    is_active: bool | None = Field(default=None)
