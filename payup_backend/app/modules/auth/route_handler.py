"""class that encapsulated api router"""

from fastapi import APIRouter, HTTPException
from twilio.base.exceptions import TwilioRestException

from .model import OTPRequestBase, OTPVerifyRequest, OTPResponse, AuthResponse
from ..auth.service import AuthService


router = APIRouter()
auth_service = AuthService()


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp_endpoint(otp_request: OTPRequestBase):
    try:
        return await auth_service.send_otp_sms(otp_request.phone_number)
    except TwilioRestException as twilio_error:
        raise HTTPException(
            status_code=twilio_error.status,
            detail=twilio_error.msg,
        ) from twilio_error


@router.post("/verify-otp", response_model=AuthResponse)
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
