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


router = APIRouter()
auth_service = AuthService()


@router.post("/send-otp", status_code=status.HTTP_200_OK, response_model=BaseResponse)
async def send_otp_endpoint(otp_request: OTPRequestBase):
    try:
        return await auth_service.send_otp_sms(otp_request.phone_number)
    except TwilioRestException as twilio_error:
        raise HTTPException(
            status_code=twilio_error.status,
            detail=twilio_error.msg,
        ) from twilio_error


@router.post("/verify-otp", status_code=status.HTTP_200_OK, response_model=BaseResponse)
async def verify_otp_endpoint(
    otp_verify: OTPVerifyRequest,
):
    try:
        return await auth_service.verify_otp(otp_verify.phone_number, otp_verify.otp)

    except TwilioRestException as twilio_error:
        raise HTTPException(
            status_code=twilio_error.status,
            detail=twilio_error.msg,
        ) from twilio_error


@router.post(
    "/register_number", status_code=status.HTTP_201_CREATED, response_model=BaseResponse
)
async def register_number_endpoint(create_account_request: RegisterNumberRequestBase):
    try:
        return await auth_service.verify_id_token_create_account(
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


@router.post(
    "/set-credentials", status_code=status.HTTP_201_CREATED, response_model=AuthResponse
)
async def set_credentials_endpoint(
    credential_body: CredentialUpdate,
):
    try:
        return await auth_service.set_credentials_txn(
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
