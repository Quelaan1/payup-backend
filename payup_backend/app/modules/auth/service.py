"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from sqlalchemy.orm import sessionmaker
from twilio.base.exceptions import TwilioRestException

from ...cockroach_sql.database import database, PoolConnection
from ...config.constants import get_settings
from ...helperClass.twilio import TwilioService
from ..user.service import UserService
from .model import AuthResponse
from ..user.model import UserCreate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

constants = get_settings()


class AuthService:
    """
    The class methods interact with twilio endpoints.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.twilio_service = TwilioService()
        self.user_service = UserService()

        self.engine = database.engine
        self.connect = PoolConnection()

        self.sessionmaker = sessionmaker(bind=self.connect)
        # self.item_repo = ItemRepo()

    async def send_otp_sms(self, phone_number: str):
        """send otp via sms"""
        try:
            return await self.twilio_service.send_otp_sms(phone_number)
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error

    async def verify_otp(self, phone_number: str, otp: str):
        """verify phone otp via sms"""
        try:
            res = AuthResponse(is_successful=False)
            otp_res = await self.twilio_service.verify_otp(phone_number, otp)
            logger.info("otp res : %s", otp_res)

            if not otp_res.is_successful:
                res.message = otp_res.message
                return res
            user = await self.user_service.get_user(phone_number=phone_number)
            if user is None:
                user = await self.user_service.create_user(
                    UserCreate(phone_number=phone_number)
                )
            res.user_data = user
            res.is_successful = True
            logger.info("res : %s", res)
            return res
        except TwilioRestException as twilio_error:
            logger.error(twilio_error.args)
            raise twilio_error
