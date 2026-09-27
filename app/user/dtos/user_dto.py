from pydantic import Field, SecretStr

from app.core.dtos import BaseDTO, BaseModelDTO


class BaseUserDTO(BaseDTO):
    """Base fields for user api"""

    username: str = Field(description="Unique username")


class UserDTO(BaseModelDTO, BaseUserDTO):
    """Fields provided in the API for an application user"""

    id: int = Field(description="Primary key")
    can_login: bool = Field(description="Whether they have a usable password or not")
    is_active: bool = Field(
        description="Determines whether the user can login, and whether their metrics are counted in grouped aggregations",
        default=True,
    )


class SetPasswordMixin:
    """Add a field to a DTO for allowing setting a valid password"""

    password: SecretStr | None = Field(default=None, min_length=6)


class CreateUserDTO(SetPasswordMixin, BaseUserDTO):
    """Fields needed to create a new user"""

    pass


class UpdateUserDTO(BaseUserDTO):
    """Fields available to update for a user"""

    is_active: bool | None = Field(default=None)


class UpdateMeDTO(SetPasswordMixin, BaseUserDTO):
    """Fields a user can update themselves"""

    username: str | None = Field(default=None)
