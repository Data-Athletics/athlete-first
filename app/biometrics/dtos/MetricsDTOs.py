from datetime import datetime, timedelta
from typing import Literal, get_args

from pydantic import BaseModel, Field, model_validator

from app.core.dtos import BaseDTO

BoolMetricType = Literal[
    "bpm", "calories", "respiratory_rate", "hrv", "rhr", "effort", "skin_temp_delta"
]

BOOL_METRICS = get_args(BoolMetricType)


class TimestampData(BaseModel):
    """Base data model for biometrics"""

    timestamp: datetime


class HeartRateDTO(TimestampData):
    """Data Transfer Object for heart rate data"""

    hr_bpm: int


class RRIntervalDTO(TimestampData):
    """Data Transfer Object for resting rate data"""

    rr_ms: int
    rr_instant_bpm: float


class GravityDTO(TimestampData):
    """Data Transfer Object for gravity (body acceleration/movement) data"""

    gravity_x: float
    gravity_y: float
    gravity_z: float
    gravity_vector_magnitude_g: float


class BloodOxygenRawDTO(TimestampData):
    """Data Transfer Object for blood oxygen level data"""

    spo2_red_raw: int
    spo2_ir_raw: int


class SkinTemperatureRawDTO(TimestampData):
    """Data Transfer Object for skin temperature data"""

    skin_temp_raw: int


class RespirationRawDTO(TimestampData):
    """Data Transfer Object for respiration data"""

    resp_raw: int


class MetricsFilterDTO(BaseDTO):
    """Query parameters to filter metrics"""

    start_time: datetime = Field(
        description="Defaults to 1 day from now",
        default_factory=lambda: datetime.now() - timedelta(days=1),
    )
    end_time: datetime = Field(
        description="Defaults to now", default_factory=lambda: datetime.now()
    )

    @model_validator(mode="after")
    def verify_start_before_end_date(self):
        if self.start_time > self.end_time:
            raise ValueError("Start time must be less than end time")

        return self
