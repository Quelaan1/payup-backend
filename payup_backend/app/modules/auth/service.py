"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
import random
from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status, Depends
from fastapi.responses import JSONResponse
from ...cockroach_sql.database import database
from ...config.constants import get_settings
from ...helperClass.verifications.phone.twilio import TwilioService
from ...cockroach_sql.schemas import PhoneEntity
from ...cockroach_sql.db_enums import UserType
from ..user.service import UserService
from .model import OTPCreate, OTPResponse
from ..user.model import UserCreate
from ..auth.model import OTPVerifyResponse
from ...cockroach_sql.dao.phone_dao import PhoneRepo
from ...cockroach_sql.dao.otp_dao import OTPRepo
from ...cockroach_sql.dao.profile_dao import ProfileRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from ..profile.model import ProfileCreate
from ..phone.model import PhoneCreate, Phone as PhoneModel, PhoneUpdate

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

    phone_repo: Annotated[PhoneRepo, Depends()]
    user_repo: Annotated[UserRepo, Depends()]
    profile_repo: Annotated[ProfileRepo, Depends()]
    otp_repo: Annotated[OTPRepo, Depends()]

    twilio_service: Annotated[TwilioService, Depends()]
    user_service: Annotated[UserService, Depends()]

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.engine = database.engine
        self.sessionmaker = sessionmaker(bind=self.engine)

    async def send_otp_sms(self, phone_number: str) -> OTPResponse:
        """send otp via sms"""
        try:
            # create random otp and store in db with expiry time
            now = datetime.now()
            future_time = now + timedelta(minutes=30)
            otp_new = random.randint(100000, 999999)

            with self.sessionmaker() as session:
                # query for phone number if already exist get if, else create phone entity in db
                db_phone_models = self.phone_repo.get_obj_by_filter(
                    session=session, col_filters=[(PhoneEntity.m_number, phone_number)]
                )
                logger.info(db_phone_models)
                if len(db_phone_models) == 0:
                    db_phone = self.create_profile_txn(phone_number)
                else:
                    db_phone = db_phone_models[0]
                db_otp_model = await self.otp_repo.update_or_create_obj(
                    session=session,
                    p_model=OTPCreate(
                        id=db_phone.id,
                        m_otp=otp_new,
                        expires_at=future_time,
                    ),
                )

            logger.info(db_otp_model.model_dump())
            response = await self.twilio_service.send_otp_sms(
                phone_number, str(otp_new)
            )
            return response
        except Exception as err:
            logger.error("error : %s", err)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": str(err.args[0])},
            )

    async def verify_otp(self, phone_number: str, otp: int) -> OTPVerifyResponse:
        """verify phone otp via sms"""
        try:
            # get phone otp data from db
            with self.sessionmaker() as session:
                otp_model = await self.otp_repo.get_otp_by_phone(
                    session=session, phone_number=phone_number
                )

                if otp_model.m_otp != otp:
                    logger.info("otp didn't matched")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="otp match failed",
                    )
                logger.info("otp matched successfully")
                # change database states.
                phone_model = await self.phone_repo.update_obj(
                    session=session,
                    obj_id=otp_model.id,
                    p_model=PhoneUpdate(is_primary=True, verified=True),
                )

                data = self.profile_repo.get_profile_by_user(
                    session=session, user_id=phone_model.user_id
                )

            return OTPVerifyResponse.model_validate(data)

        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err.args[0],
            ) from err

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
