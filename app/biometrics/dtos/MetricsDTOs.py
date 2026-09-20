from datetime import datetime

from pydantic import BaseModel


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
