from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import ModelBase


class BiometricsBase(ModelBase):
    """Shared fields and constraints for user biometric measurements."""

    __abstract__ = True

    user_id: Mapped[int] = mapped_column(ForeignKey("af_user.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @declared_attr.directive
    def __table_args__(cls):
        return (
            UniqueConstraint(
                "user_id", "timestamp", name=f"uq_{cls.__tablename__}_user_timestamp"
            ),
        )


class HeartRate(BiometricsBase):
    """Heart Rate Metric"""

    bpm: Mapped[int] = mapped_column()


class RRInterval(BiometricsBase):
    """RR Interval Metric"""

    rr_ms: Mapped[int] = mapped_column()
    rr_instant_bpm: Mapped[float] = mapped_column()


class Gravity(BiometricsBase):
    """Gravity Metric"""

    gravity_x: Mapped[float] = mapped_column()
    gravity_y: Mapped[float] = mapped_column()
    gravity_z: Mapped[float] = mapped_column()
    gravity_vector_magnitude_g: Mapped[float] = mapped_column()


class BloodOxygenRaw(BiometricsBase):
    """Blood Oxygen Raw Metric"""

    spo2_red_raw: Mapped[int] = mapped_column()
    spo2_ir_raw: Mapped[int] = mapped_column()


class SkinTemperatureRaw(BiometricsBase):
    """Skin Temperature Raw Metric"""

    skin_temp_raw: Mapped[int] = mapped_column()


class RespirationRaw(BiometricsBase):
    """Respiration Raw Metric"""

    resp_raw: Mapped[int] = mapped_column()
