import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from payup_backend.app.dependency.authentication import JWTAuth, UserClaim
from payup_backend.app.modules.device.model import (
    DeviceListResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
)
from payup_backend.app.modules.device.service import DeviceService

logger = logging.getLogger(__name__)


class DeviceHandler:
    def __init__(self, name: str) -> None:
        self.name = name
        self.device_service = DeviceService()
        self.router = APIRouter()

        self.router.add_api_route(
            "/health", self.hello, methods=["GET"], tags=["health-check"]
        )

        self.router.add_api_route(
            "/",
            self.register_device,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model=DeviceRegistrationResponse,
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/{device_id}",
            self.update_device_last_used,
            status_code=status.HTTP_200_OK,
            methods=["PUT"],
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/",
            self.get_user_devices,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/{device_id}",
            self.delete_user_device,
            status_code=status.HTTP_200_OK,
            methods=["DELETE"],
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/",
            self.delete_user_devices,
            status_code=status.HTTP_200_OK,
            methods=["DELETE"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def register_device(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
        device: DeviceRegistrationRequest,
    ) -> DeviceRegistrationResponse:
        logger.info("token user_id : %s", token_user.user_id)
        response = await self.device_service.register_device(
            device=device, user_id=UUID(token_user.user_id)
        )

        return response

    async def update_device_last_used(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
        device_id: str,
    ) -> DeviceRegistrationResponse:
        logger.info("token user_id : %s", token_user.user_id)
        response = await self.device_service.update_last_used(
            device_id=device_id, user_id=UUID(token_user.user_id)
        )

        return response

    async def get_user_devices(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
    ) -> DeviceListResponse:
        logger.info("token user_id : %s", token_user.user_id)
        response = await self.device_service.get_user_devices(
            user_id=UUID(token_user.user_id)
        )

        return response

    async def delete_user_device(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
        device_id: str,
    ) -> DeviceRegistrationResponse:
        logger.info("token user_id : %s", token_user.user_id)
        response = await self.device_service.delete_device(
            device_id=device_id, user_id=UUID(token_user.user_id)
        )

        return response

    async def delete_user_devices(
        self,
        token_user: Annotated[
            UserClaim,
            Depends(JWTAuth.get_current_user),
        ],
    ) -> DeviceRegistrationResponse:
        logger.info("token user_id : %s", token_user.user_id)
        response = await self.device_service.delete_user_devices(
            user_id=UUID(token_user.user_id)
        )

        return response
