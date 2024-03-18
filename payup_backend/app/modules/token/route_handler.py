"""class that encapsulated api router"""

import logging
from fastapi import APIRouter, status, Depends

from .model import (
    TokenBody,
    TokenRefreshRequest,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from .service import TokenService

logger = logging.getLogger(__name__)


class TokenHandler:
    def __init__(self, name: str):
        self.name = name
        self.token_service = TokenService()

        self.router = APIRouter()

        self.router.add_api_route(
            "/healthz", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/refresh",
            endpoint=self.refresh_token_endpoint,
            response_model=TokenBody,
            status_code=status.HTTP_201_CREATED,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/verify",
            endpoint=self.verify_token_endpoint,
            status_code=status.HTTP_200_OK,
            response_model=TokenVerifyResponse,
            methods=["POST"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def verify_token_endpoint(self, req_body: TokenVerifyRequest):
        res_body = await self.token_service.verify_tokens(
            access_token_string=req_body.token
        )
        logger.info(res_body.model_dump())
        return res_body

    async def refresh_token_endpoint(self, req_body: TokenRefreshRequest):
        res_body = await self.token_service.refresh_tokens(
            refresh_token_string=req_body.refresh_token
        )
        logger.info(res_body.model_dump())

        return res_body
