from typing import Literal

from app.core.dtos import BaseDTO


class HealthDTO(BaseDTO):
    status: Literal["healthy", "unhealthy"]
