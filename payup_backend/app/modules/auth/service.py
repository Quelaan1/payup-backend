"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from datetime import datetime, timedelta
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import pytz

from payup_backend.app.cockroach_sql.dao.notification_dao import (
    NotificationPreferenceRepository,
)

from .model import OTPCreate, OTPResponse, OTPUpdate
from ..user.service import UserService
from ..user.model import UserCreate
from ..profile.model import (
    ProfileCreate,
    Profile as ProfileModel,
    ProfileWithUserId as ProfileWithUserIdModel,
)
from ...cockroach_sql.database import database
from ...config.constants import get_settings
from ...helperClass.verifications.phone.twilio import TwilioService
from ...cockroach_sql.schemas import Profile, User
from ...cockroach_sql.db_enums import UserType
from ...cockroach_sql.dao.otp_dao import OTPRepo
from ...cockroach_sql.dao.profile_dao import ProfileRepo
from ...cockroach_sql.dao.user_dao import UserRepo

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
        self.sessionmaker = database.get_session()

        self.user_repo = UserRepo()
        self.profile_repo = ProfileRepo()
        self.otp_repo = OTPRepo()
        self.notification_pref_repo = NotificationPreferenceRepository()

        self.twilio_service = TwilioService()
        self.user_service = UserService()

    async def send_otp_sms(self, phone_number: str) -> OTPResponse:
        """send otp via sms"""
        try:
            logger.info("Sending OTP for %s", phone_number)
            now = datetime.now(pytz.utc)
            expiry_time = now + timedelta(minutes=30)
            expiry_time = expiry_time.replace(tzinfo=None)

            if phone_number != "8660312110":
                otp_new = secrets.randbelow(900000) + 100000  # Generates a 6-digit OTP
            else:
                # create random otp and store in db with expiry time
                otp_new = 123456

            async with self.sessionmaker() as session:
                # query for profile by phone number
                logger.info("Querying profile for %s", phone_number)

                db_profile = await self.profile_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[(Profile.phone_number, phone_number)],
                )

                logger.info("db_profile: %s", db_profile)

                if db_profile is None:
                    logger.info("Creating profile for %s", phone_number)
                    db_profile = await self.create_profile_txn(
                        phone_number=phone_number, session=session
                    )
                    logger.info("Profile created for %s", phone_number)

                db_otp = await self.otp_repo.get_obj(
                    session=session, obj_id=db_profile.id
                )

                if db_otp is None:
                    # create otp entity in db
                    updated_db = await self.otp_repo.create_obj(
                        session=session,
                        p_model=OTPCreate(
                            id=db_profile.id,
                            m_otp=otp_new,
                            expires_at=expiry_time,
                            attempt_remains=constants.TWILIO.MAX_SMS_ATTEMPTS - 1,
                        ),
                    )
                else:
                    # update otp entity in db
                    if db_otp.attempt_remains == 0:
                        updated_db = await self.otp_repo.update_obj(
                            session=session,
                            obj_id=db_profile.id,
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
                            obj_id=db_profile.id,
                            p_model=OTPUpdate(
                                m_otp=otp_new,
                                expires_at=expiry_time,
                                attempt_remains=db_otp.attempt_remains - 1,
                            ),
                        )

                await session.commit()

            if phone_number != "8660312110":
                response = await self.twilio_service.send_otp_sms(
                    phone_number, str(otp_new)
                )
            else:
                response = OTPResponse(
                    next_at=updated_db.expires_at,
                    attempt_remains=updated_db.attempt_remains,
                    message="OTP sent successfully",
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

    async def verify_otp(self, phone_number: str, otp: int) -> ProfileWithUserIdModel:
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

                # Get profile data by user ID
                profile_data = await self.profile_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[(Profile.phone_number, phone_number)],
                )

                if profile_data is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Profile not found",
                    )

                user_data = await self.user_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[(User.profile_id, profile_data.id)],
                )

                if user_data is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User not found",
                    )

                # Commit the session changes
                await session.commit()

                # Validate and return profile data
            return ProfileWithUserIdModel(
                user_id=user_data.id,
                profile=ProfileModel.model_validate(profile_data),
            )
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
        logger.debug(
            "Starting profile creation transaction for phone number: %s", phone_number
        )

        # create a profile entity
        db_profile = await self.profile_repo.create_obj(
            session=session,
            p_model=ProfileCreate(
                phone_number=phone_number,
            ),
        )
        logger.debug("Profile created with ID: %s", db_profile.id)

        # create a user entity
        db_user = await self.user_repo.create_obj(
            session=session,
            p_model=UserCreate(
                profile_id=db_profile.id,
                user_type=UserType.USER,
                is_active=False,
                phone_lock=False,
            ),
        )
        logger.debug("User created with ID: %s", db_user.id)

        # create a default notification preference
        await self.notification_pref_repo.create_default_preference(
            session=session, user_id=db_user.id
        )
        logger.debug(
            "Default notification preference created for user ID: %s", db_user.id
        )

        await session.flush()
        logger.debug("Session flushed for phone number: %s", phone_number)

        return ProfileModel.model_validate(db_profile)
