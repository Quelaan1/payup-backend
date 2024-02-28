"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from fastapi import HTTPException, status
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ..modules.auth.model import OTPResponse, OTPVerifyResponse
from ..config.constants import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

constants = get_settings()


class TwilioService:
    """
    The class methods interact with twilio endpoints.
    """

    def __init__(self):
        """
        provide Twilio client

        """
        self.client = Client(constants.TWILIO.ACCOUNT_SID, constants.TWILIO.AUTH_TOKEN)
        # self.service_id

    async def send_otp_sms(self, phone_number: str):
        """send otp via sms"""
        try:
            verification = self.client.verify.v2.services(
                constants.TWILIO.SMS_SERVICE_SID
            ).verifications.create(to="+91" + phone_number, channel="sms")
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error

        if verification.status == "pending":
            return OTPResponse(message="OTP sent successfully")

    async def verify_otp(self, phone_number: str, otp: str):
        """verify phone otp via sms"""
        try:
            verification = self.client.verify.v2.services(
                constants.TWILIO.SMS_SERVICE_SID
            ).verification_checks.create(to="+91" + phone_number, code=otp)

            if verification.status == "approved":
                return OTPVerifyResponse(
                    message="OTP verified successfully", is_successful=True
                )

            logger.info("verification status : %s", verification.status)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP verification failed",
            )
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error
