"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import pytz

from .model import OTPCreate, OTPResponse, OTPUpdate
from ..user.service import UserService
from ..user.model import UserCreate
from ..profile.model import ProfileCreate, Profile as ProfileModel
from ..phone.model import PhoneCreate, Phone as PhoneModel, PhoneUpdate
from ...cockroach_sql.database import database
from ...config.constants import get_settings
from ...helperClass.verifications.phone.twilio import TwilioService
from ...cockroach_sql.schemas import PhoneEntity
from ...cockroach_sql.db_enums import UserType
from ...cockroach_sql.dao.phone_dao import PhoneRepo
from ...cockroach_sql.dao.otp_dao import OTPRepo
from ...cockroach_sql.dao.profile_dao import ProfileRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from ...config.errors import NotFoundError

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
        self.sessionmaker = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

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
            now = datetime.now(pytz.utc)
            expiry_time = now + timedelta(minutes=30)
            expiry_time = expiry_time.replace(tzinfo=None)
            otp_new = secrets.randbelow(900000) + 100000  # Generates a 6-digit OTP

            async with self.sessionmaker() as session:
                # query for phone number if already exist get, else create phone entity in db
                db_phone_models = await self.phone_repo.get_obj_by_filter(
                    session=session, col_filters=[(PhoneEntity.m_number, phone_number)]
                )

                if len(db_phone_models) == 0:
                    db_phone = await self.create_profile_txn(
                        phone_number=phone_number, session=session
                    )
                else:
                    db_phone = db_phone_models[0]

                db_otp = await self.otp_repo.get_obj(
                    session=session, obj_id=db_phone.id
                )

                if db_otp is None:
                    # create otp entity in db
                    updated_db = await self.otp_repo.create_obj(
                        session=session,
                        p_model=OTPCreate(
                            id=db_phone.id,
                            m_otp=otp_new,
                            expires_at=expiry_time,
                            attempt_remains=constants.TWILIO.MAX_SMS_ATTEMPTS - 1,
                        ),
                    )
                else:
                    # update otp entity in db
                    if db_otp.attempt_remains == 0:
                        # if db_otp.expires_at > now:
                        #     logger.error("Limit reached. Please try after sometime.")
                        #     res = OTPResponse(
                        #         next_at=db_otp.expires_at,
                        #         attempt_remains=db_otp.attempt_remains,
                        #         message="Limit reached. Please try after sometime.",
                        #     )
                        #     raise HTTPException(
                        #         status_code=status.HTTP_400_BAD_REQUEST,
                        #         detail=res.model_dump_json(),
                        #     )
                        updated_db = await self.otp_repo.update_obj(
                            session=session,
                            obj_id=db_phone.id,
                            p_model=OTPUpdate(
                                m_otp=otp_new,
                                expires_at=expiry_time,
                                attempt_remains=constants.TWILIO.MAX_SMS_ATTEMPTS - 1,
                            ),
                        )
                    else:
                        if db_otp.updated_at + timedelta(minutes=1) > now:
                            logger.error("Not Allowed. Wait for 1 minute.")
                            res = OTPResponse(
                                next_at=db_otp.updated_at + timedelta(minutes=1),
                                attempt_remains=db_otp.attempt_remains,
                                message="Not Allowed. Wait for 1 minute.",
                            )
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=res.model_dump_json(),
                            )
                        updated_db = await self.otp_repo.update_obj(
                            session=session,
                            obj_id=db_phone.id,
                            p_model=OTPUpdate(
                                m_otp=otp_new,
                                expires_at=expiry_time,
                                attempt_remains=db_otp.attempt_remains - 1,
                            ),
                        )

                await session.commit()

            response = await self.twilio_service.send_otp_sms(
                phone_number, str(otp_new)
            )

            nx = (
                updated_db.updated_at + timedelta(minutes=1)
                if updated_db.attempt_remains > 0
                else expiry_time
            )
            return OTPResponse(
                next_at=nx,
                attempt_remains=updated_db.attempt_remains,
                message=response.message,
            )
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("Send OTP: %s", err)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred.\nPlease try again later.",
            ) from err

    async def verify_otp(self, phone_number: str, otp: int) -> ProfileModel:
        """Verify phone OTP via SMS."""
        try:
            async with self.sessionmaker() as session:
                # Get phone OTP data from the database
                otp_model = await self.otp_repo.delete_obj_related_by_number(
                    session=session,
                    phone_number=phone_number,
                    col_filters=[(self.otp_repo.repo_schema.m_otp, otp)],
                )

                # Check if OTP model exists
                if otp_model is None:
                    logger.debug("OTP didn't match")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The OTP you entered is incorrect. Please try again.",
                    )

                # Update database state
                phone_model = await self.phone_repo.update_obj(
                    session=session,
                    obj_id=otp_model.id,
                    p_model=PhoneUpdate(is_primary=True, verified=True),
                )

                # Get profile data by user ID
                data = await self.profile_repo.get_profile_by_user(
                    session=session, user_id=phone_model.user_id
                )

                # Commit the session changes
                await session.commit()

                # Validate and return profile data
                return ProfileModel.model_validate(data)

        except HTTPException:
            # Re-raise HTTPExceptions (already handled)
            raise

        except Exception as err:
            # Log and raise other exceptions
            logger.error("Error during OTP verification: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again later.",
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
    #                 (self.phone_repo.repo_schema.m_number, phone_number),
    #                 (self.phone_repo.repo_schema.is_primary, True),
    #                 (self.phone_repo.repo_schema.verified, True)
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

    async def create_profile_txn(self, phone_number: str, session: AsyncSession):

        # create a profile entity
        # create a user entity
        # create a phone
        db_profile = await self.profile_repo.create_obj(
            session=session, p_model=ProfileCreate()
        )

        db_user = await self.user_repo.create_obj(
            session=session,
            p_model=UserCreate(
                profile_id=db_profile.id,
                user_type=UserType.USER,
                is_active=False,
                phone_lock=False,
            ),
        )

        db_phone = await self.phone_repo.create_obj(
            session=session,
            p_model=PhoneCreate(
                m_number=phone_number,
                user_id=db_user.id,
                primary=True,
                verified=False,
            ),
        )
        await session.flush()
        return PhoneModel.model_validate(db_phone)
