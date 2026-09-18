import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal[
    "heart_rate",
    "rr_interval",
    "gravity",
    "optical_raw",
    "skin_temperature_raw",
    "respiration_raw",
]


class TimestampData(BaseModel):
    """Base data model for biometrics"""

    timestamp: datetime.datetime


class HeartRate(TimestampData):
    """Data model for heart rate data"""

    hr_bpm: int


class RRInterval(TimestampData):
    """Data model for resting rate data"""

    rr_ms: int
    rr_instant_bpm: float


class Gravity(TimestampData):
    """Data model for gravity (body acceleration/movement) data"""

    gravity_x: float
    gravity_y: float
    gravity_z: float
    gravity_vector_magnitude_g: float


class BloodOxygenRaw(TimestampData):
    """Data model for blood oxygen level data"""

    spo2_red_raw: int
    spo2_ir_raw: int


class SkinTemperatureRaw(TimestampData):
    """Data model for skin temperature data"""

    skin_temp_raw: int


class RespirationRaw(TimestampData):
    """Data model for respiration data"""

    resp_raw: int


class NoopData(BaseModel):
    """Data model for bulk database insertion"""

    heart_rate: list[HeartRate] = Field(default_factory=list)
    rr_interval: list[RRInterval] = Field(default_factory=list)
    gravity: list[Gravity] = Field(default_factory=list)
    optical_raw: list[BloodOxygenRaw] = Field(default_factory=list)
    skin_temperature_raw: list[SkinTemperatureRaw] = Field(default_factory=list)
    respiration_raw: list[RespirationRaw] = Field(default_factory=list)

    def add(self, source_type: SourceType, value: BaseModel) -> None:
        match source_type:
            case "heart_rate":
                assert isinstance(value, HeartRate)
                self.heart_rate.append(value)

            case "rr_interval":
                assert isinstance(value, RRInterval)
                self.rr_interval.append(value)

            case "gravity":
                assert isinstance(value, Gravity)
                self.gravity.append(value)

            case "optical_raw":
                assert isinstance(value, BloodOxygenRaw)
                self.optical_raw.append(value)

            case "skin_temperature_raw":
                assert isinstance(value, SkinTemperatureRaw)
                self.skin_temperature_raw.append(value)

            case "respiration_raw":
                assert isinstance(value, RespirationRaw)
                self.respiration_raw.append(value)
