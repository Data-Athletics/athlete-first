from pydantic import BaseModel, ConfigDict, Field


class BaseDTO(BaseModel):
    """Base class inherited by all DTOs."""

    model_config = ConfigDict(from_attributes=True)


class SimpleResponseDTO(BaseDTO):
    """Plain JSON response"""

    detail: str = Field(description="Response message")
    code: int = Field(description="HTTP status code")
