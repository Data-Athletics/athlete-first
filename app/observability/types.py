from enum import StrEnum


class HealthStatus(StrEnum):
    """Indicate system health."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
