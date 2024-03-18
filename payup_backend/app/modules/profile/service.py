"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from .model import ProfileUpdate
from ...cockroach_sql.database import database
from ...config.constants import get_settings
from ...cockroach_sql.dao.profile_dao import ProfileRepo

logger = logging.getLogger(__name__)

constants = get_settings()


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
        self.engine = database.engine
        self.sessionmaker = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self._repo = ProfileRepo()

    async def get_user_profile(self, obj_id: UUID):
        """
        Wraps a `session` call that gets a profile.

        Arguments:
            obj_id {UUID} -- The profile's unique ID.
        """
        async with self.sessionmaker() as session:
            user = await self._repo.get_obj(session=session, obj_id=obj_id)
            await session.commit()
        return user

    async def update_user_profile(self, obj_id: UUID, update_model: ProfileUpdate):
        """
        Wraps a `session` call that updates users in a particular city as a list of dictionaries.

        Arguments:
            obj_id {UUID} -- The profile's id.
            update_model {ProfileUpdate} -- profile's update model

        Returns:
            List -- A list of dictionaries containing user data.
        """
        async with self.sessionmaker() as session:
            user = await self._repo.update_obj(
                session=session, obj_id=obj_id, p_model=update_model
            )
            await session.commit()
        return user
