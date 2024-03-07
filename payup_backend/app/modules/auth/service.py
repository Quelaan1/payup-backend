"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from sqlalchemy.orm import sessionmaker
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException, status
from ...cockroach_sql.database import database, PoolConnection
from ...config.constants import get_settings
from ...helperClass.verifications.phone.twilio import TwilioService
from ...helperClass.verifications.phone.firebase_service import FirebaseService

from ..user.service import UserService
from .model import AuthResponse
from ..user.model import UserCreate
from ..auth.model import VerifierCreate, VerifierUpdate
from ...cockroach_sql.db_enums import VerifierType
from ...cockroach_sql.dao.verifier_dao import VerifierRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from ...cockroach_sql.db_enums import VerifierType

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
        self.firebase_service = FirebaseService()

        self.engine = database.engine
        self.connect = PoolConnection()

        self.sessionmaker = sessionmaker(bind=self.connect)
        self.verifier_repo = VerifierRepo()
        self.user_repo = UserRepo()

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

    async def create_user_txn(
        self, user_body: UserCreate, verifier_body: VerifierCreate
    ):
        """
        Wraps a `run_transaction` call that creates an user.

        Arguments:
            user_body {UserCreate} -- The user's validated pydantic model.
            verifier_body {VerifierCreate} -- The user's validated providers pydantic model.

        """

        with self.sessionmaker() as session:
            new_user = self.user_repo.create_obj(p_model=user_body, session=session)
            verifier_body.user_id = new_user.id
            _ = self.verifier_repo.create_obj(session=session, p_model=verifier_body)
            return new_user

    async def verify_id_token_create_account(
        self, id_token: str, phone_number: str, verifier: int
    ):
        """verify phone otp via sms"""
        try:

            if verifier == VerifierType.FIREBASE.value:
                token_details = await self.firebase_service.verify_id_token(
                    id_token=id_token
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="verifier type not recognised",
                )
            uid = token_details.get("uid")

            # check for existing user with same number. if exists resolve account ownership with kyc details. flag other account to update phone number
            user = await self.user_service.get_user(phone_number=phone_number)
            if user is not None:
                # resolve account ownership with kyc details
                logger.info("already registered phone number")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="phone number already registered",
                )
            new_user = await self.create_user_txn(
                user_body=UserCreate(),
                verifier_body=VerifierCreate(
                    phone_verifier=VerifierType.FIREBASE.value,
                    v_id=uid,
                    phone_number=phone_number,
                ),
            )
            res = AuthResponse(is_successful=True, user_data=new_user)

            logger.info("res : %s", res)
            return res
        except Exception as service_error:
            logger.error(service_error.args)
            raise Exception from service_error

    async def set_credentials_txn(self, verifier_body: VerifierUpdate):
        """
        Wraps a `run_transaction` call that creates an user.

        Arguments:
            user_body {UserCreate} -- The user's validated pydantic model.
            verifier_body {VerifierCreate} -- The user's validated providers pydantic model.

        """

        with self.sessionmaker() as session:
            creds = self.verifier_repo.get_obj_by_filter(
                session=session, cols=["user_id"], col_vals=[verifier_body.user_id]
            )
            for _, cred in enumerate(creds):
                if cred.phone_number == verifier_body.phone_number:
                    obj_id = cred.id
                else:
                    return False
            self.verifier_repo.update_obj(
                session=session, p_model=verifier_body, obj_id=obj_id
            )
            return True
