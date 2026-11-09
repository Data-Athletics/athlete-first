from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class BaseDTO(BaseModel):
    """Base class inherited by all DTOs."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class SimpleResponseDTO(BaseDTO):
    """Plain JSON response"""

    detail: str = Field(description="Response message")
    code: int = Field(description="HTTP status code")


class PermissionDeniedReason(StrEnum):
    """Reasons a user could be denied permission"""

    POLICY_RESTRICTION = "policy_restriction"
    NULL_POLICY = "null_policy"
    INVALID_POLICY = "invalid_policy"
    UNKNOWN = "unknown"


class PermissionDeniedResponseDTO(SimpleResponseDTO):
    """Extra fields provided for 403 errors"""

    reason: PermissionDeniedReason = Field(
        description="Simple response", default=PermissionDeniedReason.UNKNOWN
    )


class BaseModelDTO(BaseDTO):
    """Fields present on all DTOs representing database models"""

    id: int = Field(description="Primary key")
    created_at: AwareDatetime = Field(description="Date the object was created")
    updated_at: AwareDatetime = Field(description="Last time the object was updated")
