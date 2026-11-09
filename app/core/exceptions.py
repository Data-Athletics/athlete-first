from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from app.core.dtos import PermissionDeniedReason


class PermissionException(HTTPException):
    """Exception raised when user is not allowed to do an action"""

    def __init__(
        self,
        detail: Any = None,
        reason: PermissionDeniedReason = PermissionDeniedReason.UNKNOWN,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.reason = reason
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers
        )
