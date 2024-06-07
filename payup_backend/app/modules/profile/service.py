"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from .model import ProfileUpdate
from ...cockroach_sql.database import database
from ...cockroach_sql.dao.profile_dao import ProfileRepo


logger = logging.getLogger(__name__)


class ProfileService:
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

        self._repo = ProfileRepo()

    async def get_user_profile(self, obj_id: UUID):
        """
        Wraps a `session` call that gets a profile.

        Arguments:
            obj_id {UUID} -- The profile's unique ID.
        """
        try:
            async with self.sessionmaker() as session:
                user = await self._repo.get_obj(session=session, obj_id=obj_id)
                await session.commit()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found"
                )
            return user
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err

    async def update_user_profile(self, obj_id: UUID, update_model: ProfileUpdate):
        """
        Wraps a `session` call that updates users in a particular city as a list of dictionaries.

        Arguments:
            obj_id {UUID} -- The profile's id.
            update_model {ProfileUpdate} -- profile's update model

        Returns:
            List -- A list of dictionaries containing user data.
        """

        try:
            async with self.sessionmaker() as session:
                user = await self._repo.update_obj(
                    session=session, obj_id=obj_id, p_model=update_model
                )
                await session.commit()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found"
                )
            return user
        except HTTPException as e:
            raise e
        except IntegrityError as e:
            # Extract the details of the error
            error_message = str(e)
            logger.error("Error message: %s", error_message)

            # Check if the error message indicates a unique constraint violation for "profiles_email_key"
            if "profiles_email_key" in error_message.lower():
                # Raise an HTTPException with proper context for a duplicate email
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                ) from e
            # Handle other types of IntegrityErrors
            logger.error("Other IntegrityError occurred")
            # Handle the specific case here
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Other IntegrityError occurred",
            ) from e

        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err
