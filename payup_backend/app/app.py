from fastapi import APIRouter, Depends

from .modules.auth.route_handler import AuthHandler
from .modules.item.route_handler import ItemHandler
from .modules.profile.route_handler import ProfileHandler
from .modules.promotion.route_handler import PromotionHandler
from .modules.token.route_handler import TokenHandler
from .modules.kyc.route_handler import KycHandler

# from .dependency.authentication import oauth2_scheme

router = APIRouter()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

auth = AuthHandler("auth")
profile = ProfileHandler("profile")
kyc = KycHandler("kyc")
item = ItemHandler("item")
token = TokenHandler("token")
promotion = PromotionHandler()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(item.router, prefix="/item", tags=["item"])
router.include_router(token.router, prefix="/token", tags=["token"])
router.include_router(kyc.router, prefix="/kyc", tags=["kyc"])
router.include_router(promotion.router, prefix="/promotion", tags=["promotion"])
