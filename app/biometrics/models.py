from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ModelBase


class UserRelationshipMixin:
    """Mixin for user specific biometrics"""

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))


class TimestampMixin:
    """Mixin for timestamp column in metrics"""

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class HeartRate(ModelBase, TimestampMixin, UserRelationshipMixin):
    """Heart Rate Metric"""

    bpm: Mapped[int] = mapped_column()


class RRInterval(ModelBase, TimestampMixin, UserRelationshipMixin):
    """RR Interval Metric"""

    rr_ms: Mapped[int] = mapped_column()
    rr_instant_bpm: Mapped[float] = mapped_column()


class Gravity(ModelBase, TimestampMixin, UserRelationshipMixin):
    """Gravity Metric"""

    gravity_x: Mapped[float] = mapped_column()
    gravity_y: Mapped[float] = mapped_column()
    gravity_z: Mapped[float] = mapped_column()
    gravity_vector_magnitude_g: Mapped[float] = mapped_column()


class BloodOxygenRaw(ModelBase, TimestampMixin, UserRelationshipMixin):
    """Blood Oxygen Raw Metric"""

    spo2_red_raw: Mapped[int] = mapped_column()
    spo2_ir_raw: Mapped[int] = mapped_column()


class SkinTemperatureRaw(ModelBase, TimestampMixin, UserRelationshipMixin):
    """Skin Temperature Raw Metric"""

    skin_temp_raw: Mapped[int] = mapped_column()


class RespirationRaw(ModelBase, TimestampMixin, UserRelationshipMixin):
    """Respiration Raw Metric"""

    resp_raw: Mapped[int] = mapped_column()
