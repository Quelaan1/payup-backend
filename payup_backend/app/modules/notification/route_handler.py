import logging
from fastapi import APIRouter, status, Depends
from typing import Annotated, List
from .model import (
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
)
from payup_backend.app.modules.notification.service import NotificationService
from ...dependency.authentication import UserClaim, JWTAuth

logger = logging.getLogger(__name__)


class NotificationHandler:
    def __init__(self, name: str):
        self.name = name
        self.notification_service = NotificationService()
        self.router = APIRouter()

        self.router.add_api_route(
            "/health", self.hello, methods=["GET"], tags=["health-check"]
        )

        self.router.add_api_route(
            "/preferences",
            endpoint=self.get_preferences_endpoint,
            response_model=NotificationPreferenceResponse,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/preferences",
            endpoint=self.update_preferences_endpoint,
            response_model=NotificationPreferenceResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )

        self.router.add_api_route(
            "/send",
            endpoint=self.send_push_notification_endpoint,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def get_preferences_endpoint(
        self,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ) -> NotificationPreferenceResponse:
        preferences = await self.notification_service.get_preference(token_user.user_id)
        return preferences

    async def update_preferences_endpoint(
        self,
        req_body: NotificationPreferenceRequest,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ) -> NotificationPreferenceResponse:
        preferences = await self.notification_service.update_preference(
            token_user.user_id, req_body
        )
        return preferences

    async def send_push_notification_endpoint(
        self,
        title: str,
        message: str,
        notification_type: str,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        await self.notification_service.send_push_notification(
            token_user.user_id, title, message, notification_type
        )
        return {"status": "Notification sent"}
