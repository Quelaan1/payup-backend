import logging
from fastapi import APIRouter, status, Depends
from .model import InitiatePaymentRequest, InitiatePaymentResponse
from payup_backend.app.modules.easebuzz.service import EasebuzzService
from ...dependency.authentication import UserClaim, JWTAuth
from typing import Annotated

logger = logging.getLogger(__name__)


class EasebuzzHandler:
    def __init__(self, name: str):
        self.name = name
        self.easebuzz_service = EasebuzzService()
        self.router = APIRouter()

        # Health-check route
        self.router.add_api_route(
            "/health", self.hello, methods=["GET"], tags=["health-check"]
        )

        # Route to add a new payee
        self.router.add_api_route(
            "/initiate-payment",
            endpoint=self.initiate_payment,
            response_model=InitiatePaymentResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def initiate_payment(
        self,
        req_body: InitiatePaymentRequest,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ) -> InitiatePaymentResponse:
        easebuzz_model = await self.easebuzz_service.initiate_payment(
            token_user,
            req_body.amount,
            req_body.productinfo,
            req_body.payment_mode,
        )

        logger.info("Payment initiated successfully")

        return easebuzz_model
