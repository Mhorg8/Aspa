from fastapi import APIRouter

from app.core.exceptions import ErrorResponse
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

router = APIRouter(
    prefix="/api",
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
router.include_router(auth_router)
router.include_router(users_router)
