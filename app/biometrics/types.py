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
    timestamp: datetime.datetime


class HeartRate(TimestampData):
    hr_bpm: int


class RRInterval(TimestampData):
    rr_ms: int
    rr_instant_bpm: float


class Gravity(TimestampData):
    gravity_x: float
    gravity_y: float
    gravity_z: float
    gravity_vector_magnitude_g: float


class OpticalRaw(TimestampData):
    spo2_red_raw: int
    spo2_ir_raw: int


class SkinTemperatureRaw(TimestampData):
    skin_temp_raw: int


class RespirationRaw(TimestampData):
    resp_raw: int


class NoopData(BaseModel):
    heart_rate: list[HeartRate] = Field(default_factory=list)
    rr_interval: list[RRInterval] = Field(default_factory=list)
    gravity: list[Gravity] = Field(default_factory=list)
    optical_raw: list[OpticalRaw] = Field(default_factory=list)
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
                assert isinstance(value, OpticalRaw)
                self.optical_raw.append(value)

            case "skin_temperature_raw":
                assert isinstance(value, SkinTemperatureRaw)
                self.skin_temperature_raw.append(value)

            case "respiration_raw":
                assert isinstance(value, RespirationRaw)
                self.respiration_raw.append(value)
