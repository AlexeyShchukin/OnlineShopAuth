from fastapi import APIRouter

from .auth import auth_router
from .users import user_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
router.include_router(user_router, prefix="/user")
