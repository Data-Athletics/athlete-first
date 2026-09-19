from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ModelBase


class TimestampMixin:
    """Mixin for timestamp column in metrics"""

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class HeartRate(ModelBase, TimestampMixin):
    """Heart Rate Metric"""

    bpm: Mapped[int] = mapped_column()


class RRInterval(ModelBase, TimestampMixin):
    """RR Interval Metric"""

    rr_ms: Mapped[int] = mapped_column()
    rr_instant_bpm: Mapped[float] = mapped_column()


class Gravity(ModelBase, TimestampMixin):
    """Gravity Metric"""

    gravity_x: Mapped[float] = mapped_column()
    gravity_y: Mapped[float] = mapped_column()
    gravity_z: Mapped[float] = mapped_column()
    gravity_vector_magnitude_g: Mapped[float] = mapped_column()


class BloodOxygenRaw(ModelBase, TimestampMixin):
    """Blood Oxygen Raw Metric"""

    spo2_red_raw: Mapped[int] = mapped_column()
    spo2_ir_raw: Mapped[int] = mapped_column()


class SkinTemperatureRaw(ModelBase, TimestampMixin):
    """Skin Temperature Raw Metric"""

    skin_temp_raw: Mapped[int] = mapped_column()


class RespirationRaw(ModelBase, TimestampMixin):
    """Respiration Raw Metric"""

    resp_raw: Mapped[int] = mapped_column()
