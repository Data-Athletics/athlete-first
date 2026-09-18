from fastapi import APIRouter

from .user import users_router

router = APIRouter()
router.include_router(users_router)

__all__ = ["router"]
