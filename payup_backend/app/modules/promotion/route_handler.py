import logging
from fastapi import APIRouter, status

from payup_backend.app.modules.promotion.model import PromotionResponse
from payup_backend.app.modules.promotion.service import PromotionService

logger = logging.getLogger(__name__)


def hello():
    logger.debug(
        "Hello : %s",
    )

    return {"Hello"}


class PromotionHandler:
    def __init__(self):
        self.promotion_service = PromotionService()

        self.router = APIRouter()

        self.router.add_api_route(
            "/health", hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/",
            endpoint=self.get_promotion_endpoint,
            response_model=PromotionResponse,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )

    async def get_promotion_endpoint(self):
        return {"promotions": await self.promotion_service.get_promotion()}
