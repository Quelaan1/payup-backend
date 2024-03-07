"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from fastapi import HTTPException, status
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ....modules.auth.model import BaseResponse
from ....config.constants import get_settings


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

    async def send_otp_sms_verification_type(self, phone_number: str):
        """send otp via sms"""
        try:
            verification = self.client.verify.v2.services(
                constants.TWILIO.SMS_SERVICE_SID
            ).verifications.create(to="+91" + phone_number, channel="sms")
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error

        if verification.status == "pending":
            return BaseResponse(message="OTP sent successfully")

    async def send_otp_sms(self, phone_number: str, otp: str):
        """send otp via sms"""
        try:
            verification = self.client.messages.create(
                to="+91" + phone_number,
                from_=constants.TWILIO.PHONE_NUMBER,
                body=f"""
                Dear customer, your PayUp verification code is {otp}. 
                Message is valid for next 30 minutes. Single use only.""",
                # constants.TWILIO.SMS_SERVICE_SID
            )
            logger.info("[TWILIO RESPONSE : %s]", verification.status)
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error

        if verification.status in ["pending", "queued"]:
            return BaseResponse(message="OTP sent successfully", is_successful=True)

    async def verify_otp(self, phone_number: str, otp: str):
        """verify phone otp via sms"""
        try:
            verification = self.client.verify.v2.services(
                constants.TWILIO.SMS_SERVICE_SID
            ).verification_checks.create(to="+91" + phone_number, code=otp)

            if verification.status == "approved":
                return BaseResponse(
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


# from twilio.rest import Client

# account_sid = "AC3ae61ecaf87782344127fe35756aa6cb"
# auth_token = "[AuthToken]"
# client = Client(account_sid, auth_token)

# message = client.messages.create(
#     from_="+19144990713",
#     body="Dear customer, your PayUp verification code is 123456. ",
#     to="+919990912228",
# )

# print(message.sid)

# 201 - CREATED - The request was successful. We created a new resource and the response body contains the representation.
# {
#   "body": "Sent from your Twilio trial account - Dear customer, your PayUp verification code is 123456.",
#   "num_segments": "1",
#   "direction": "outbound-api",
#   "from": "+19144990713",
#   "date_updated": "Thu, 07 Mar 2024 04:07:39 +0000",
#   "price": null,
#   "error_message": null,
#   "uri": "/2010-04-01/Accounts/AC3ae61ecaf87782344127fe35756aa6cb/Messages/SM76ed1f2355c4ef89b9c5155172279200.json",
#   "account_sid": "AC3ae61ecaf87782344127fe35756aa6cb",
#   "num_media": "0",
#   "to": "+919990912228",
#   "date_created": "Thu, 07 Mar 2024 04:07:39 +0000",
#   "status": "queued",
#   "sid": "SM76ed1f2355c4ef89b9c5155172279200",
#   "date_sent": null,
#   "messaging_service_sid": null,
#   "error_code": null,
#   "price_unit": "USD",
#   "api_version": "2010-04-01",
#   "subresource_uris": {
#     "media": "/2010-04-01/Accounts/AC3ae61ecaf87782344127fe35756aa6cb/Messages/SM76ed1f2355c4ef89b9c5155172279200/Media.json"
#   }
# }
