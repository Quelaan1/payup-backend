"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import sessionmaker
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException, status
from ...cockroach_sql.database import database, PoolConnection
from ...config.constants import get_settings
from ...helperClass.verifications.phone.twilio import TwilioService
from ...cockroach_sql.schemas import PhoneEntity
from ...cockroach_sql.db_enums import UserType
from ..user.service import UserService
from .model import AuthResponse, OTPCreate
from ..user.model import UserCreate
from ..auth.model import VerifierCreate, VerifierUpdate
from ...cockroach_sql.db_enums import VerifierType
from ...cockroach_sql.dao.phone_dao import PhoneRepo
from ...cockroach_sql.dao.otp_dao import OTPRepo
from ...cockroach_sql.dao.profile_dao import ProfileRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from ..profile.model import ProfileCreate
from ..phone.model import PhoneCreate, Phone as PhoneModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

constants = get_settings()


class AuthService:
    """
    The class methods interact with multiple services to facilitate auth endpoints.
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
        self.phone_repo = PhoneRepo()
        self.user_repo = UserRepo()
        self.profile_repo = ProfileRepo()
        self.otp_repo = OTPRepo()

    async def send_otp_sms(self, phone_number: str):
        """send otp via sms"""
        try:
            # create random otp and store in db with expiry time
            now = datetime.now()
            future_time = now + timedelta(minutes=30)
            otp_new = random.randint(100000, 999999)

            with self.sessionmaker() as session:
                # query for phone number if already exist get if, else create phone entity in db
                db_phone_models = self.phone_repo.get_obj_by_filter(
                    session=session, col_filters=[(PhoneEntity.number, phone_number)]
                )
                if len(db_phone_models) == 0:
                    db_phone = self.create_profile_txn(phone_number)
                else:
                    db_phone = db_phone_models[0]
                db_otp_model = self.otp_repo.update_or_create_obj(
                    session=session,
                    p_model=OTPCreate(
                        id=db_phone.id,
                        phone_number=phone_number,
                        otp=otp_new,
                        expires_at=future_time,
                    ),
                )
                logger.info(db_otp_model.model_dump())

            logger.info(db_otp_model.model_dump())
            return await self.twilio_service.send_otp_sms(phone_number, str(otp_new))
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

    # async def create_user_txn(
    #     self, user_body: UserCreate, verifier_body: VerifierCreate
    # ):
    #     """
    #     Wraps a `run_transaction` call that creates an user.

    #     Arguments:
    #         user_body {UserCreate} -- The user's validated pydantic model.
    #         verifier_body {VerifierCreate} -- The user's validated providers pydantic model.

    #     """

    #     with self.sessionmaker() as session:
    #         new_user = self.user_repo.create_obj(p_model=user_body, session=session)
    #         verifier_body.user_id = new_user.id
    #         _ = self.verifier_repo.create_obj(session=session, p_model=verifier_body)
    #         return new_user

    # async def set_credentials_txn(self, verifier_body: VerifierUpdate):
    #     """
    #     Wraps a `run_transaction` call that creates an user.

    #     Arguments:
    #         user_body {UserCreate} -- The user's validated pydantic model.
    #         verifier_body {VerifierCreate} -- The user's validated providers pydantic model.

    #     """

    #     with self.sessionmaker() as session:
    #         creds = self.verifier_repo.get_obj_by_filter(
    #             session=session, cols=["user_id"], col_vals=[verifier_body.user_id]
    #         )
    #         for _, cred in enumerate(creds):
    #             if cred.phone_number == verifier_body.phone_number:
    #                 obj_id = cred.id
    #             else:
    #                 return False
    #         self.verifier_repo.update_obj(
    #             session=session, p_model=verifier_body, obj_id=obj_id
    #         )
    #         return True

    def create_profile_txn(self, phone_number: str):
        """
        Select a row of the profiles table, and return the row as a Profile object.

        Arguments:
            session {.Session} -- The active session for the database connection.

        Keyword Arguments:
            phone_number {String} -- The profile's phone_number. (default: {None})
            profile_id {UUID} -- The profile's unique ID. (default: {None})

        Returns:
            Phone -- A Phone object.
        """

        # create a profile entity
        # create a user entity
        # create a phone
        with self.sessionmaker() as session:
            db_profile = self.profile_repo.create_obj(
                session=session, p_model=ProfileCreate()
            )

            db_user = self.user_repo.create_obj(
                session=session,
                p_model=UserCreate(
                    profile_id=db_profile.id,
                    user_type=UserType.USER,
                    is_active=False,
                    phone_lock=False,
                ),
            )

            db_phone = self.phone_repo.create_obj(
                session=session,
                p_model=PhoneCreate(
                    m_number=phone_number,
                    user_id=db_user.id,
                    primary=True,
                    verified=False,
                ),
            )

            return PhoneModel.model_validate(db_phone)
