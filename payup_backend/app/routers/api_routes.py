from fastapi import APIRouter

from ..modules.auth.route_handler import Auth
from ..modules.user.route_handler import router as user_router


router = APIRouter()

auth = Auth("auth")
router.include_router(auth.router, prefix="/auth")

router.include_router(
    router=user_router,
    prefix="/user",
)
