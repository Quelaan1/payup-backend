"""class that encapsulated api router"""

import logging
from fastapi import APIRouter, status, Depends

from .pan.pan_model import PANVerifyRequestSchema, PANVerifyResponseSchema
from .service import KycService

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
            "/",
            endpoint=self.create_kyc_endpoint,
            response_model=PANVerifyResponseSchema,
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

    async def create_kyc_endpoint(self, req_body: PANVerifyRequestSchema):
        res_body = await self.kyc_service.verify_kyc(kyc_entity=req_body.kyc)
        logger.info(res_body.model_dump())
        return res_body

    # async def all_kyc_endpoint(self, req_body: KycRefreshRequest):
    #     res_body = await self.kyc_service.refresh_kycs(
    #         refresh_kyc_string=req_body.refresh_kyc
    #     )
    #     logger.info(res_body.model_dump())

    #     return res_body
