from datetime import datetime

from pydantic import BaseModel, Field


class HRVResponseDTO(BaseModel):
    hrv: float | None = Field(description="HRV value for a specific user")
    start: datetime = Field(description="Start time for HRV measurement")
    end: datetime = Field(description="End time for HRV measurement")
