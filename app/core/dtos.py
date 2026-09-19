from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class BaseDTO(BaseModel):
    """Base class inherited by all DTOs."""

    model_config = ConfigDict(from_attributes=True)


class SimpleResponseDTO(BaseDTO):
    """Plain JSON response"""

    detail: str = Field(description="Response message")
    code: int = Field(description="HTTP status code")


class BaseModelDTO(BaseDTO):
    """Fields present on all DTOs representing database models"""

    id: int = Field(description="Primary key")
    created_at: AwareDatetime = Field(description="Date the object was created")
    updated_at: AwareDatetime = Field(description="Last time the object was updated")
