import logging

from fastapi import APIRouter, Depends, status
from typing import Annotated
from payup_backend.app.modules.device_token.model import (
    DeviceTokenCreateRequest,
    DeviceTokenCreateResponse,
    DeviceTokenUpdateRequest,
    DeviceTokenUpdateResponse,
)
from payup_backend.app.dependency.authentication import JWTAuth, UserClaim
from payup_backend.app.modules.device_token.service import DeviceTokenService

logger = logging.getLogger(__name__)


class DeviceTokenHandler:
    def __init__(self, name: str) -> None:
        self.name = name
        self.device_token_service = DeviceTokenService()
        self.router = APIRouter()

        self.router.add_api_route(
            "/",
            self.create_device_token,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model=DeviceTokenCreateResponse,
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/",
            self.update_device_token,
            status_code=status.HTTP_200_OK,
            methods=["PUT"],
            response_model=DeviceTokenUpdateResponse,
            response_model_exclude_none=True,
        )

    async def create_device_token(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
        device_token: DeviceTokenCreateRequest,
    ) -> DeviceTokenCreateResponse:
        logger.info("Creating device token")
        response = await self.device_token_service.create_device_token(device_token)
        return response

    async def update_device_token(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
        device_token: DeviceTokenUpdateRequest,
    ) -> DeviceTokenUpdateResponse:
        logger.info("Updating device token")
        response = await self.device_token_service.update_device_token(device_token)
        return response
