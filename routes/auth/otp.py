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


@router.post("/auth/verify-pan", response_model=OTPVerifyResponseSchema)
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


# curl --request GET \
#  --url 'https://api.sandbox.co.in/pans/binpt2390c/verify?consent=y&reason=For%20KYC%20of%20User' \
#  --header 'Authorization: eyJhbGciOiJIUzUxMiJ9.eyJhdWQiOiJBUEkiLCJyZWZyZXNoX3Rva2VuIjoiZXlKaGJHY2lPaUpJVXpVeE1pSjkuZXlKaGRXUWlPaUpCVUVraUxDSnpkV0lpT2lKeVlXaDFiSEJ5WVd0aGMyZ3hNVUJuYldGcGJDNWpiMjBpTENKaGNHbGZhMlY1SWpvaWEyVjVYMnhwZG1WZmJFRTFVVFZhZG1oT1YxSnpORVpSVTNacmNIWnJObTVKT1c5UVMzcE1Ra1FpTENKcGMzTWlPaUpoY0drdWMyRnVaR0p2ZUM1amJ5NXBiaUlzSW1WNGNDSTZNVGN6T1RFMk5UUXpPU3dpYVc1MFpXNTBJam9pVWtWR1VrVlRTRjlVVDB0RlRpSXNJbWxoZENJNk1UY3dOelUwTXpBek9YMC5MX1piUjM3Z2Q1bTB4OXlVSG03UzRRSEtNTTJ3anByY09iTTNlWng3bjVURUNFQjFnZ0F0SHhKV3lkYUdZek9aODlVT0pnclMxcWwtMC1WTnB6VnZXQSIsInN1YiI6InJhaHVscHJha2FzaDExQGdtYWlsLmNvbSIsImFwaV9rZXkiOiJrZXlfbGl2ZV9sQTVRNVp2aE5XUnM0RlFTdmtwdms2bkk5b1BLekxCRCIsImlzcyI6ImFwaS5zYW5kYm94LmNvLmluIiwiZXhwIjoxNzA3NjI5NDM5LCJpbnRlbnQiOiJBQ0NFU1NfVE9LRU4iLCJpYXQiOjE3MDc1NDMwMzl9.obvkII7VanJ2PImqqJNUMXBblYLw_CXcuxosvO3d0uM7R93Da-tnjGHcfRNthjO0iBCWuFsKkHK_j_gFjyTkig' \
#  --header 'accept: application/json' \
#  --header 'x-api-key: key_live_lA5Q5ZvhNWRs4FQSvkpvk6nI9oPKzLBD' \
#  --header 'x-api-version: 1.0'
