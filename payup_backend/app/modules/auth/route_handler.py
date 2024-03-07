"""class that encapsulated api router"""

from fastapi import APIRouter, HTTPException, status
from twilio.base.exceptions import TwilioRestException

from .model import (
    OTPRequestBase,
    OTPVerifyRequest,
    AuthResponse,
    RegisterNumberRequestBase,
    CredentialUpdate,
    VerifierUpdate,
)
from ..auth.service import AuthService
from ...models.py_models import BaseResponse

# class Foo:
#     # Step 3: Add dependencies as class attributes
#     x: int = Depends(get_x)

#     @router.get("/somewhere")
#     def bar(self) -> int:
#         # Step 4: Use `self.<dependency_name>` to access shared dependencies
#         return self.x


# class Hello:

#     def __init__(self, name: str):
#         self.name = name
#         self.router = APIRouter()
#         self.router.add_api_route("/hello", self.hello, methods=["GET"])

#     def hello(self):
#         return {"Hello": self.name}


# app = FastAPI()
# hello = Hello("World")
# app.include_router(hello.router)


class Auth:
    def __init__(self, name: str):
        self.name = name
        self.auth_service = AuthService()
        self.router = APIRouter()
        self.router.add_api_route("/", self.hello, methods=["GET"])
        self.router.add_api_route(
            "/otp",
            endpoint=self.send_otp_endpoint,
            response_model=BaseResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/verify/otp",
            endpoint=self.verify_otp_endpoint,
            status_code=status.HTTP_200_OK,
            response_model=BaseResponse,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/register_number",
            endpoint=self.register_number_endpoint,
            status_code=status.HTTP_201_CREATED,
            response_model=BaseResponse,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/set-credentials",
            endpoint=self.set_credentials_endpoint,
            status_code=status.HTTP_201_CREATED,
            response_model=AuthResponse,
            methods=["POST"],
        )

    def hello(self):
        return {"Hello": self.name}

    async def send_otp_endpoint(self, otp_request: OTPRequestBase):
        try:
            return await self.auth_service.send_otp_sms(otp_request.phone_number)
        except TwilioRestException as twilio_error:
            raise HTTPException(
                status_code=twilio_error.status,
                detail=twilio_error.msg,
            ) from twilio_error

    async def verify_otp_endpoint(self, otp_verify: OTPVerifyRequest):
        try:
            return await self.auth_service.verify_otp(
                otp_verify.phone_number, otp_verify.otp
            )

        except TwilioRestException as twilio_error:
            raise HTTPException(
                status_code=twilio_error.status,
                detail=twilio_error.msg,
            ) from twilio_error

    async def register_number_endpoint(
        self, create_account_request: RegisterNumberRequestBase
    ):
        try:
            return await self.auth_service.verify_id_token_create_account(
                id_token=create_account_request.id_token,
                phone_number=create_account_request.phone_number,
                verifier=create_account_request.verifier,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.args,
            ) from e

    async def set_credentials_endpoint(self, credential_body: CredentialUpdate):
        try:
            return await self.auth_service.set_credentials_txn(
                verifier_body=VerifierUpdate(
                    m_pin=credential_body.m_pin,
                    phone_number=credential_body.phone_number,
                    phone_lock=credential_body.phone_lock,
                )
            )

        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err.args,
            ) from err
