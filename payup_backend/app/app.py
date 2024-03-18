from fastapi import APIRouter, Depends

from .modules.auth.route_handler import AuthHandler
from .modules.item.route_handler import ItemHandler
from .modules.profile.route_handler import ProfileHandler
from .modules.token.route_handler import TokenHandler

# from .dependency.authentication import oauth2_scheme

router = APIRouter()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

auth = AuthHandler("auth")
profile = ProfileHandler("profile")
item = ItemHandler("item")
token = TokenHandler("token")

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(item.router, prefix="/item", tags=["item"])
router.include_router(token.router, prefix="/token", tags=["token"])
