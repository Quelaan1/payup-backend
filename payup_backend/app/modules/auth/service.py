"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
import random
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
from ..profile.model import ProfileCreate, Profile as ProfileModel
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

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.engine = database.engine
        self.sessionmaker = sessionmaker(bind=self.engine)

        self.phone_repo = PhoneRepo()
        self.user_repo = UserRepo()
        self.profile_repo = ProfileRepo()
        self.otp_repo = OTPRepo()

        self.twilio_service = TwilioService()
        self.user_service = UserService()

    async def send_otp_sms(self, phone_number: str) -> OTPResponse:
        """send otp via sms"""
        try:
            # create random otp and store in db with expiry time
            now = datetime.utcnow()
            future_time = now + timedelta(minutes=30)
            otp_new = random.randint(100000, 999999)

            with self.sessionmaker() as session:
                # query for phone number if already exist get if, else create phone entity in db
                db_phone_models = self.phone_repo.get_obj_by_filter(
                    session=session, col_filters=[(PhoneEntity.m_number, phone_number)]
                )
                logger.debug(db_phone_models)
                if len(db_phone_models) == 0:
                    db_phone = self.create_profile_txn(
                        phone_number=phone_number, session=session
                    )
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
                session.commit()

            logger.debug(db_otp_model.model_dump())
            response = await self.twilio_service.send_otp_sms(
                phone_number, str(otp_new)
            )
            return response
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args,
            ) from err

    async def verify_otp(self, phone_number: str, otp: int) -> ProfileModel:
        """verify phone otp via sms"""
        try:
            # get phone otp data from db
            with self.sessionmaker() as session:

                otp_model = await self.otp_repo.delete_obj_related_by_number(
                    session=session,
                    phone_number=phone_number,
                    col_filters=[(self.otp_repo._schema.m_otp, otp)],
                )

                if otp_model is None:
                    logger.debug("otp didn't matched")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="otp match failed",
                    )

                logger.debug("otp matched successfully")
                # change database states.
                phone_model = await self.phone_repo.update_obj(
                    session=session,
                    obj_id=otp_model.id,
                    p_model=PhoneUpdate(is_primary=True, verified=True),
                )

                data = self.profile_repo.get_profile_by_user(
                    session=session, user_id=phone_model.user_id
                )
                session.commit()

            return ProfileModel.model_validate(data)
        except (
            Exception
        ) as err:  # This will catch any exception that is not an HTTPException
            logger.error("error : %s", err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(err.args),
            ) from err

    # async def set_credentials_txn(self, phone_number: str, pin: int, user_id: UUID):
    #     """
    #     Wraps a `run_transaction` call that creates an user.

    #     Arguments:
    #         user_body {UserCreate} -- The user's validated pydantic model.
    #         verifier_body {VerifierCreate} -- The user's validated providers pydantic model.

    #     """

    #     with self.sessionmaker() as session:
    #         creds = self.phone_repo.get_obj_by_filter(
    #             session=session, col_filters=[
    #                 (self.phone_repo._schema.m_number, phone_number),
    #                 (self.phone_repo._schema.is_primary, True),
    #                 (self.phone_repo._schema.verified, True)
    #             ]
    #         )

    #         if len(creds) == 0:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail="phone number not verified as a primary account number"
    #             )
    #         elif len(creds) > 0:
    #             raise HTTPException(
    #                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                 detail="database discrepancy",
    #             )

    #         db_phone = creds[0]
    #         for _, cred in enumerate(creds):
    #             if cred.phone_number == verifier_body.phone_number:
    #                 obj_id = cred.id
    #             else:
    #                 return False
    #         self.verifier_repo.update_obj(
    #             session=session, p_model=verifier_body, obj_id=obj_id
    #         )
    #         return True

    def create_profile_txn(self, phone_number: str, session: Session):

        # create a profile entity
        # create a user entity
        # create a phone
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
        session.flush()
        return PhoneModel.model_validate(db_phone)
