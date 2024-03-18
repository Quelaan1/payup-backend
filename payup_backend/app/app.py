from fastapi import APIRouter, Depends

from .modules.auth.route_handler import AuthHandler
from .modules.item.route_handler import ItemHandler
from .modules.token.route_handler import TokenHandler
from .modules.user.route_handler import router as user_router

# from .dependency.authentication import oauth2_scheme

router = APIRouter()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

auth = AuthHandler("auth")
item = ItemHandler("item")
token = TokenHandler("token")

router.include_router(auth.router, prefix="/auth", tags=["auth"])
# router.include_router(
#     item.router, prefix="/item", dependencies=[Depends(oauth2_scheme)], tags=["item"]
# )
router.include_router(token.router, prefix="/token", tags=["token"])
router.include_router(item.router, prefix="/item", tags=["item"])
router.include_router(
    router=user_router,
    prefix="/user",
)
