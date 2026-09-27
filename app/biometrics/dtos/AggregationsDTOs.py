from datetime import datetime

from pydantic import BaseModel, Field


class IntervalData(BaseModel):
    start: datetime = Field(description="Start time for HRV measurement")
    end: datetime = Field(description="End time for HRV measurement")


class SkinTempDeltaResponseDTO(BaseModel):
    """Response object for skin temp delta data"""

    skin_temp_delta: float | None = Field(
        description="Skin temp delta value for a specific user"
    )


class HRVResponseDTO(IntervalData):
    """Response object for HRV data"""

    hrv: float | None = Field(description="HRV value for a specific user")


class RHRResponseDTO(IntervalData):
    """Response object for RHR data"""

    rhr: float | None = Field(description="RHR value for a specific user")


class RespiratoryRateResponseDTO(BaseModel):
    """Response object for Respiratory Rate data"""

    respiratory_rate: float | None = Field(
        description="Respiratory rate for a specific user"
    )


class EffortStrainResponseDTO(BaseModel):
    """Response object for Strain/Effort data"""

    effort: float | None = Field(description="Strain/Effort value for a specific user")


class GraphResponseDTO(IntervalData):
    """Response object for (x, y) coordinate data"""

    x: list[datetime] = Field(description="x values of datetimes for graph")
    y: list[float] = Field(description="y values of floats for graph")
