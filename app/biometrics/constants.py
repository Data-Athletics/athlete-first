from app.biometrics.types import (
    BloodOxygenRaw,
    Gravity,
    HeartRate,
    RespirationRaw,
    RRInterval,
    SkinTemperatureRaw,
    SourceType,
)

NOOP_SOURCE_COLUMN = "stream"
"""Column in csv where the type of biometric data lives"""

NOOP_DATA_ROWS: dict[SourceType, list[str]] = {
    "heart_rate": [
        "hr_bpm",
    ],
    "rr_interval": [
        "rr_ms",
        "rr_instant_bpm",
    ],
    "gravity": [
        "gravity_x",
        "gravity_y",
        "gravity_z",
        "gravity_vector_magnitude_g",
    ],
    "optical_raw": [
        "spo2_red_raw",
        "spo2_ir_raw",
    ],
    "skin_temperature_raw": [
        "skin_temp_raw",
    ],
    "respiration_raw": [
        "resp_raw",
    ],
}
"""Mapping of stream data type to columns of data we want to pull out"""

NOOP_DATA_MODELS = {
    "heart_rate": HeartRate,
    "rr_interval": RRInterval,
    "gravity": Gravity,
    "optical_raw": BloodOxygenRaw,
    "skin_temperature_raw": SkinTemperatureRaw,
    "respiration_raw": RespirationRaw,
}
"""Mapping of stream data type to data model that should be created"""

NOOP_TIME_COLUMN = "iso_utc"
"""Column in csv where we pull timestamp from"""
