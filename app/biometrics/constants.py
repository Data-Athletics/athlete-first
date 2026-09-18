from app.biometrics.types import (
    Gravity,
    HeartRate,
    OpticalRaw,
    RespirationRaw,
    RRInterval,
    SkinTemperatureRaw,
    SourceType,
)

NOOP_SOURCE_COLUMN = "stream"

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

NOOP_DATA_MODELS = {
    "heart_rate": HeartRate,
    "rr_interval": RRInterval,
    "gravity": Gravity,
    "optical_raw": OpticalRaw,
    "skin_temperature_raw": SkinTemperatureRaw,
    "respiration_raw": RespirationRaw,
}

NOOP_TIME_COLUMN = "iso_utc"
