import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated, List

from .model import AddPayeeRequest, PayeeModel
from payup_backend.app.modules.payee.service import PayeeService
from payup_backend.app.modules.kyc.service import KycService
from ...dependency.authentication import UserClaim, JWTAuth

logger = logging.getLogger(__name__)


class PayeeHandler:
    def __init__(self, name: str):
        self.name = name
        self.payee_service = PayeeService()
        self.router = APIRouter()
        self.kyc_service = KycService()

        # Health-check route
        self.router.add_api_route(
            "/health", self.hello, methods=["GET"], tags=["health-check"]
        )

        # Route to get all payees for a user
        self.router.add_api_route(
            "/",
            endpoint=self.get_payees_endpoint,
            response_model=List[PayeeModel],
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )

        # Route to add a new payee
        self.router.add_api_route(
            "/",
            endpoint=self.add_payee_endpoint,
            response_model=PayeeModel,
            status_code=status.HTTP_201_CREATED,
            methods=["POST"],
            response_model_exclude_none=True,
        )

        # Route to delete a payee
        self.router.add_api_route(
            "/{payee_id}",
            endpoint=self.delete_payee_endpoint,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["DELETE"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def get_payees_endpoint(
        self,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ) -> List[PayeeModel]:
        payees = await self.payee_service.get_payees(token_user.user_id)
        return payees

    async def add_payee_endpoint(
        self,
        req_body: AddPayeeRequest,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ) -> PayeeModel:
        logger.info("Adding payee: %s", token_user)

        payee = await self.payee_service.add_payee(
            token_user.user_id, req_body, token_user.profile_id
        )

        return payee

    async def delete_payee_endpoint(
        self,
        payee_id: str,
        token_user: Annotated[UserClaim, Depends(JWTAuth.get_current_user)],
    ):
        logger.info("Deleting payee: %s", payee_id)

        await self.payee_service.delete_payee(token_user.user_id, payee_id, token_user.profile_id)  # type: ignore
        return {"status": "Payee deleted successfully"}
