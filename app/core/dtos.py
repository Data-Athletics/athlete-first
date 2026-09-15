from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base class inherited by all DTOs."""

    model_config = ConfigDict(from_attributes=True)
