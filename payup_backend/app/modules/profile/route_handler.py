"""class that encapsulated api router"""

import logging
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException

from payup_backend.app.modules import user

from .model import (
    ProfileDeleteResponse,
    ProfileUpdateRequest,
    Profile as ProfileResponse,
    ProfileWithUserId,
)
from .service import ProfileService
from ...dependency.authentication import UserClaim, JWTAuth
from ...config.errors import TokenException

logger = logging.getLogger(__name__)


class ProfileHandler:
    def __init__(self, name: str):
        self.name = name
        self.profile_service = ProfileService()

        self.router = APIRouter()

        self.router.add_api_route(
            "/health", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/",
            endpoint=self.get_token_profile_endpoint,
            response_model=ProfileWithUserId,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/{obj_id}",
            endpoint=self.get_profile_endpoint,
            response_model=ProfileWithUserId,
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/{obj_id}",
            endpoint=self.update_profile_endpoint,
            status_code=status.HTTP_201_CREATED,
            response_model=ProfileWithUserId,
            methods=["PUT"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/{obj_id}",
            endpoint=self.delete_profile_endpoint,
            response_model=ProfileDeleteResponse,
            status_code=status.HTTP_200_OK,
            methods=["DELETE"],
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def get_token_profile_endpoint(
        self,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info("token profile_id : %s", token_user.profile_id)
        response = await self.profile_service.get_user_profile(
            obj_id=UUID(token_user.profile_id)
        )
        # logger.info(response.model_dump())
        return ProfileWithUserId(user_id=UUID(token_user.user_id), profile=response)

    async def get_profile_endpoint(
        self,
        obj_id: UUID,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info("profile_id : %s", obj_id)
        logger.info("token profile_id : %s", token_user.profile_id)

        if str(obj_id) != token_user.profile_id:
            logger.info("ids didn't match")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="different profile_id"
            )
        response = await self.profile_service.get_user_profile(obj_id=obj_id)
        logger.info(response.model_dump())
        return ProfileWithUserId(user_id=UUID(token_user.user_id), profile=response)

    async def update_profile_endpoint(
        self,
        obj_id: UUID,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
        req_body: ProfileUpdateRequest,
    ):
        logger.info("profile_id : %s", obj_id)
        logger.info("token profile_id : %s", token_user.profile_id)

        if str(obj_id) != token_user.profile_id:
            logger.info("ids didn't match")
            raise TokenException(detail="different profile_id", name="token_user")

        logger.info("Update profile request: %s", req_body.model_dump())

        response = await self.profile_service.update_user_profile(
            obj_id=obj_id, update_model=req_body
        )
        logger.info(response.model_dump())
        return ProfileWithUserId(user_id=UUID(token_user.user_id), profile=response)

    async def delete_profile_endpoint(
        self,
        obj_id: UUID,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info("profile_id : %s", obj_id)
        logger.info("token profile_id : %s", token_user.profile_id)

        if str(obj_id) != token_user.profile_id:
            logger.info("ids didn't match")
            raise TokenException(detail="different profile_id", name="token_user")

        response = await self.profile_service.delete_user_profile(obj_id=obj_id)
        logger.info(response.model_dump())
        return response
