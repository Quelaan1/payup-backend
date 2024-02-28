from fastapi import APIRouter

from ..modules.auth.route_handler import router as auth_router
from ..modules.user.route_handler import router as user_router

# from ..modules.item.route_handler import router as item_router


router = APIRouter()

router.include_router(
    router=auth_router,
    prefix="/auth",
)

router.include_router(
    router=user_router,
    prefix="/user",
)
