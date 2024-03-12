from fastapi import APIRouter

from .modules.auth.route_handler import AuthHandler
from .modules.item.route_handler import ItemHandler
from .modules.user.route_handler import router as user_router


router = APIRouter()

auth = AuthHandler("auth")
item = ItemHandler("item")
router.include_router(auth.router, prefix="/auth")
router.include_router(item.router, prefix="/item")

router.include_router(
    router=user_router,
    prefix="/user",
)
