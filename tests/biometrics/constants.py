import datetime

from app.biometrics import (
    Gravity,
    HeartRate,
    NoopData,
    OpticalRaw,
    RespirationRaw,
    RRInterval,
    SkinTemperatureRaw,
)


def dt(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value)


EXPECTED_NOOP_DATA = NoopData(
    heart_rate=[
        HeartRate(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            hr_bpm=52,
        ),
        HeartRate(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            hr_bpm=52,
        ),
    ],
    rr_interval=[
        RRInterval(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            rr_ms=1291,
            rr_instant_bpm=46.48,
        ),
        RRInterval(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            rr_ms=1242,
            rr_instant_bpm=48.31,
        ),
    ],
    gravity=[
        Gravity(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            gravity_x=0.072429202,
            gravity_y=0.670554221,
            gravity_z=0.737812519,
            gravity_vector_magnitude_g=0.999628,
        ),
        Gravity(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            gravity_x=0.069887698,
            gravity_y=0.6733374,
            gravity_z=0.737695336,
            gravity_vector_magnitude_g=1.00123,
        ),
    ],
    optical_raw=[
        OpticalRaw(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            spo2_red_raw=661,
            spo2_ir_raw=723,
        ),
        OpticalRaw(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            spo2_red_raw=661,
            spo2_ir_raw=723,
        ),
    ],
    skin_temperature_raw=[
        SkinTemperatureRaw(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            skin_temp_raw=1412,
        ),
        SkinTemperatureRaw(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            skin_temp_raw=1419,
        ),
    ],
    respiration_raw=[
        RespirationRaw(
            timestamp=dt("2025-04-27T14:46:47.000Z"),
            resp_raw=3073,
        ),
        RespirationRaw(
            timestamp=dt("2025-04-27T14:46:47.048Z"),
            resp_raw=3073,
        ),
    ],
)
