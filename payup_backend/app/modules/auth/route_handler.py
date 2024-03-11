"""class that encapsulated api router"""

import logging
from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .model import (
    OTPResponse,
    OTPRequestBase,
    OTPVerifyRequest,
    OTPVerifyResponse,
    AuthResponse,
    # RegisterNumberRequestBase,
    Credential,
)
from ..auth.service import AuthService

logger = logging.getLogger(__name__)


class AuthHandler:
    def __init__(self, name: str):
        self.name = name
        self.auth_service = AuthService()
        self.router = APIRouter()
        self.router.add_api_route(
            "/healthz", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/otp",
            endpoint=self.send_otp_endpoint,
            response_model=OTPResponse,
            status_code=status.HTTP_200_OK,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/verify/otp",
            endpoint=self.verify_otp_endpoint,
            status_code=status.HTTP_200_OK,
            response_model=OTPVerifyResponse,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/signup",
            endpoint=self.set_pin_endpoint,
            status_code=status.HTTP_201_CREATED,
            response_model=AuthResponse,
            methods=["POST"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/login",
            endpoint=self.login_endpoint,
            status_code=status.HTTP_201_CREATED,
            response_model=AuthResponse,
            methods=["POST"],
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def send_otp_endpoint(self, otp_request: OTPRequestBase):
        response = await self.auth_service.send_otp_sms(otp_request.phone_number)
        logger.info(response.model_dump())
        return response

    async def verify_otp_endpoint(self, otp_verify: OTPVerifyRequest):
        response = await self.auth_service.verify_otp(
            otp_verify.phone_number, otp_verify.otp
        )
        logger.info(response.model_dump())
        return response

    async def set_pin_endpoint(self, data: Credential):
        # querying database to check if phone already exist
        response = await self.auth_service.verify_otp(data.phone_number, data.m_pin)
        logger.info(response.model_dump())
        return response

    async def login_endpoint(self, form_data: OAuth2PasswordRequestForm = Depends()):
        data = {}
        data["scopes"] = []
        for scope in form_data.scopes:
            data["scopes"].append(scope)

        logger.info(dict(form_data))

        # user = db.get(form_data.username, None)
        # if user is None:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Incorrect email or password",
        #     )

        # hashed_pass = user["password"]
        # if not verify_password(form_data.password, hashed_pass):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Incorrect email or password",
        #     )

        # return {
        #     "access_token": create_access_token(user["email"]),
        #     "refresh_token": create_refresh_token(user["email"]),
        # }


#     @app.post("/token")
# async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     user_dict = fake_users_db.get(form_data.username)
#     if not user_dict:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
#     user = UserInDB(**user_dict)
#     hashed_password = fake_hash_password(form_data.password)
#     if not hashed_password == user.hashed_password:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")

#     return {"access_token": user.username, "token_type": "bearer"}
