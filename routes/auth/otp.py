import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from starlette import status
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from schemas.auth.otp import (
    OTPRequestSchema,
    OTPResponseSchema,
    OTPVerifyRequestSchema,
    OTPVerifyResponseSchema,
)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger(__name__)

router = APIRouter()

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
service_sid = os.environ["TWILIO_SMS_SERVICE_SID"]

client = Client(account_sid, auth_token)


@router.post("/auth/send-otp", response_model=OTPResponseSchema)
async def send_otp_endpoint(otp_request: OTPRequestSchema):
    try:
        verification = client.verify.v2.services(service_sid).verifications.create(
            to="+91" + otp_request.phone_number, channel="sms"
        )
    except TwilioRestException as twilio_error:
        raise HTTPException(
            status_code=twilio_error.status,
            detail=twilio_error.msg,
        )

    if verification.status == "pending":
        return OTPResponseSchema(message="OTP sent successfully")


@router.post("/auth/verify-otp", response_model=OTPVerifyResponseSchema)
async def verify_otp_endpoint(
    otp_verify: OTPVerifyRequestSchema,
):
    try:
        verification = client.verify.v2.services(
            service_sid
        ).verification_checks.create(
            to="+91" + otp_verify.phone_number, code=otp_verify.otp
        )
    except TwilioRestException as twilio_error:
        raise HTTPException(
            status_code=twilio_error.status,
            detail=twilio_error.msg,
        )

    if verification.status == "approved":

        return OTPVerifyResponseSchema(message="OTP verified successfully")
    elif verification.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification failed",
        )
