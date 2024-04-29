"""class that encapsulated api router"""

import logging
from typing import Annotated, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, status, Depends

from .model import PhoneUpdate, PhoneCreate, Phone as PhoneModel, PhoneResponse
from .service import PhoneService
from ...dependency.authentication import get_current_active_user

logger = logging.getLogger(__name__)


class PhoneHandler:
    def __init__(self, name: str):
        self.name = name
        self.user_data: Annotated[Any, Depends(get_current_active_user)]
        self.phone_service = PhoneService()
        self.router = APIRouter()
        self.router.add_api_route(
            "/healthz", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/",
            endpoint=self.send_phone_endpoint,
            response_model=PhoneResponse,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/",
            endpoint=self.update_phone_endpoint,
            status_code=status.HTTP_200_OK,
            response_model=PhoneResponse,
            methods=["PUT"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def send_phone_endpoint(self, user_data: Annotated[Any, Depends()]):
        response = await self.phone_service.get_phone_details(user_data.user_id)
        logger.info(response.model_dump())
        return response

    async def update_phone_endpoint(self, id: UUID, update_data: PhoneUpdate):
        response = await self.phone_service.set_phone_pin(
            phone_id=id, pin=update_data.m_pin, user_id=uuid4()
        )
        logger.info(response.model_dump())
        return response
