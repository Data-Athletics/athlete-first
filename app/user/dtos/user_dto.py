from pydantic import Field

from app.core.dtos import BaseDTO


class UserDTO(BaseDTO):
    """Fields provided in the API for an application user"""

    id: int = Field(description="Primary key")
    username: str = Field(description="Unique username")

    is_active: bool = Field(
        description="Determines whether the user can login, and whether their metrics are counted in grouped aggregations"
    )
    can_login: bool = Field(description="Whether they have a usable password or not")
