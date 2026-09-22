from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.biometrics.dtos.MetricsDTOs import (
    BloodOxygenRawDTO,
    GravityDTO,
    HeartRateDTO,
    RespirationRawDTO,
    RRIntervalDTO,
    SkinTemperatureRawDTO,
)
from app.biometrics.models import (
    BloodOxygenRaw as BloodOxygenRawModel,
)
from app.biometrics.models import (
    Gravity as GravityModel,
)

# Import the SQLAlchemy models for conversion
from app.biometrics.models import (
    HeartRate as HeartRateModel,
)
from app.biometrics.models import (
    RespirationRaw as RespirationRawModel,
)
from app.biometrics.models import (
    RRInterval as RRIntervalModel,
)
from app.biometrics.models import (
    SkinTemperatureRaw as SkinTemperatureRawModel,
)

SourceType = Literal[
    "heart_rate",
    "rr_interval",
    "gravity",
    "optical_raw",
    "skin_temperature_raw",
    "respiration_raw",
]


@dataclass
class NoopDataModels:
    """Container for bulk insertion of SQLAlchemy model objects"""

    heart_rate: list[HeartRateModel] = Field(default_factory=list)
    rr_interval: list[RRIntervalModel] = Field(default_factory=list)
    gravity: list[GravityModel] = Field(default_factory=list)
    optical_raw: list[BloodOxygenRawModel] = Field(default_factory=list)
    skin_temperature_raw: list[SkinTemperatureRawModel] = Field(default_factory=list)
    respiration_raw: list[RespirationRawModel] = Field(default_factory=list)

    def to_list(self) -> list[Any]:
        return [
            *self.heart_rate,
            *self.rr_interval,
            *self.gravity,
            *self.optical_raw,
            *self.skin_temperature_raw,
            *self.respiration_raw,
        ]


class NoopData(BaseModel):
    """Container for bulk insertion of DTO objects"""

    heart_rate: list[HeartRateDTO] = Field(default_factory=list)
    rr_interval: list[RRIntervalDTO] = Field(default_factory=list)
    gravity: list[GravityDTO] = Field(default_factory=list)
    optical_raw: list[BloodOxygenRawDTO] = Field(default_factory=list)
    skin_temperature_raw: list[SkinTemperatureRawDTO] = Field(default_factory=list)
    respiration_raw: list[RespirationRawDTO] = Field(default_factory=list)

    def add(self, source_type: SourceType, value: BaseModel) -> None:
        """Append a DTO to the appropriate list based on its source type"""
        match source_type:
            case "heart_rate":
                assert isinstance(value, HeartRateDTO)
                self.heart_rate.append(value)
            case "rr_interval":
                assert isinstance(value, RRIntervalDTO)
                self.rr_interval.append(value)
            case "gravity":
                assert isinstance(value, GravityDTO)
                self.gravity.append(value)
            case "optical_raw":
                assert isinstance(value, BloodOxygenRawDTO)
                self.optical_raw.append(value)
            case "skin_temperature_raw":
                assert isinstance(value, SkinTemperatureRawDTO)
                self.skin_temperature_raw.append(value)
            case "respiration_raw":
                assert isinstance(value, RespirationRawDTO)
                self.respiration_raw.append(value)

    def to_models(self, user_id: int) -> NoopDataModels:
        """
        Convert all stored DTOs into their SQLAlchemy model counterparts.
        Returns a NoopDataModels for bulk insertion.
        """
        return NoopDataModels(
            heart_rate=[
                HeartRateModel(timestamp=dto.timestamp, user_id=user_id, bpm=dto.hr_bpm)
                for dto in self.heart_rate
            ],
            rr_interval=[
                RRIntervalModel(
                    timestamp=dto.timestamp,
                    user_id=user_id,
                    rr_ms=dto.rr_ms,
                    rr_instant_bpm=dto.rr_instant_bpm,
                )
                for dto in self.rr_interval
            ],
            gravity=[
                GravityModel(
                    timestamp=dto.timestamp,
                    user_id=user_id,
                    gravity_x=dto.gravity_x,
                    gravity_y=dto.gravity_y,
                    gravity_z=dto.gravity_z,
                    gravity_vector_magnitude_g=dto.gravity_vector_magnitude_g,
                )
                for dto in self.gravity
            ],
            optical_raw=[
                BloodOxygenRawModel(
                    timestamp=dto.timestamp,
                    user_id=user_id,
                    spo2_red_raw=dto.spo2_red_raw,
                    spo2_ir_raw=dto.spo2_ir_raw,
                )
                for dto in self.optical_raw
            ],
            skin_temperature_raw=[
                SkinTemperatureRawModel(
                    timestamp=dto.timestamp,
                    user_id=user_id,
                    skin_temp_raw=dto.skin_temp_raw,
                )
                for dto in self.skin_temperature_raw
            ],
            respiration_raw=[
                RespirationRawModel(
                    timestamp=dto.timestamp, user_id=user_id, resp_raw=dto.resp_raw
                )
                for dto in self.respiration_raw
            ],
        )
