"""class that encapsulated api router"""

import logging
from typing import Annotated
from fastapi import APIRouter, status, Depends, HTTPException

from .service import KycService
from .model import (
    KycBase,
    KycResponse,
    KycCreate,
    AadhaarKycResponse,
    AadhaarKycRequest,
)
from ...cockroach_sql.db_enums import KycType
from ...dependency.authentication import UserClaim, JWTAuth

# from .pan.

logger = logging.getLogger(__name__)


class KycHandler:
    def __init__(self, name: str):
        self.name = name
        self.kyc_service = KycService()

        self.router = APIRouter()

        self.router.add_api_route(
            "/healthz", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/pan/verify",
            endpoint=self.verify_kyc_pan_endpoint,
            response_model=KycResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/aadhaar/otp",
            endpoint=self.send_aadhaar_otp_endpoint,
            response_model=AadhaarKycResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/aadhaar/verify",
            endpoint=self.check_aadhaar_otp_endpoint,
            response_model=KycResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/pan",
            endpoint=self.create_kyc_endpoint,
            response_model=KycResponse,
            status_code=status.HTTP_201_CREATED,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        # self.router.add_api_route(
        #     "/",
        #     endpoint=self.all_kyc_endpoint,
        #     status_code=status.HTTP_200_OK,
        #     response_model=KycVerifyResponse,
        #     methods=["GET"],
        #     response_model_exclude_none=True,
        # )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def verify_kyc_pan_endpoint(
        self,
        req_body: KycBase,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):

        if req_body.entity_type != KycType.PAN:
            raise ValueError("Wrong entity_type.")
        res_body = await self.kyc_service.pan_verify(
            owner_id=token_user.profile_id, pan_id=req_body.entity_id
        )
        logger.info(res_body.model_dump())
        return res_body

    async def send_aadhaar_otp_endpoint(
        self,
        req_body: KycBase,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info(token_user.model_dump())
        if req_body.entity_type != KycType.AADHAAR:
            raise ValueError("Wrong entity_type.")
        res_body = await self.kyc_service.aadhaar_ekyc_otp(
            aadhaar_id=req_body.entity_id, owner_id=token_user.profile_id
        )
        logger.info(res_body.model_dump())
        return res_body

    async def check_aadhaar_otp_endpoint(
        self,
        req_body: AadhaarKycRequest,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info(token_user.model_dump())
        res_body = await self.kyc_service.aadhaar_ekyc_verify(
            owner_id=token_user.profile_id,
            otp=req_body.otp,
            ref_id=req_body.ref_id,
            aadhaar_number=req_body.aadhaar_number,
        )
        logger.info(res_body.model_dump())
        return res_body

    async def create_kyc_endpoint(
        self,
        req_body: KycCreate,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info(token_user.model_dump())
        res_body = await self.kyc_service.create_kyc(kyc_data=req_body)
        logger.info(res_body.model_dump())
        return res_body

    # async def all_kyc_endpoint(self, req_body: KycRefreshRequest):
    #     res_body = await self.kyc_service.refresh_kycs(
    #         refresh_kyc_string=req_body.refresh_kyc
    #     )
    #     logger.info(res_body.model_dump())

    #     return res_body
