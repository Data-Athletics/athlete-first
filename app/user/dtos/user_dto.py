from pydantic import Field, SecretStr

from app.core.dtos import BaseDTO, BaseModelDTO
from app.user.models import UserSex


class BaseUserDTO(BaseDTO):
    """Base fields for user API"""

    username: str = Field(description="Unique username")

    height: float | None = Field(default=None, description="Height in inches", gt=0)

    weight: float | None = Field(default=None, description="Weight in pounds", gt=0)

    sex: UserSex | None = Field(default=None, description="User's sex")

    age: int | None = Field(default=None, description="Age in years", gt=0)


class UserDTO(BaseModelDTO, BaseUserDTO):
    """Fields provided in the API for an application user"""

    id: int = Field(description="Primary key")

    can_login: bool = Field(description="Whether they have a usable password or not")

    is_active: bool = Field(
        description=(
            "Determines whether the user can login, and whether their metrics "
            "are counted in grouped aggregations"
        ),
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

    username: str | None = Field(default=None)
    height: float | None = Field(default=None, gt=0)
    weight: float | None = Field(default=None, gt=0)
    sex: UserSex | None = Field(default=None)
    age: int | None = Field(default=None, gt=0)
    is_active: bool | None = Field(default=None)


class UpdateMeDTO(SetPasswordMixin, BaseUserDTO):
    """Fields a user can update themselves"""

    username: str | None = Field(default=None)
    height: float | None = Field(default=None, gt=0)
    weight: float | None = Field(default=None, gt=0)
    sex: UserSex | None = Field(default=None)
    age: int | None = Field(default=None, gt=0)
