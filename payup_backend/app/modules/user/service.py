"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from pydantic import UUID4
from typing import Optional
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from ...cockroach_sql.dao.user_dao import UserRepo
from .model import UserCreate
from ...cockroach_sql.database import database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class UserService:
    """
    Wraps the database connection. The class methods wrap database transactions.
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

        self._repo = UserRepo()

    async def create_user(self, req_body: UserCreate):
        """
        Wraps a `run_transaction` call that creates an user.

        Arguments:
            reqBody {UserCreate} -- The user's validated pydantic request model.
            user_id {UUID} -- The user's unique ID.
        """
        with self.sessionmaker() as session:
            user = self._repo.create_obj(p_model=req_body, session=session)
            session.commit()
        return user

    async def get_users(self, skip, limit):
        """
        Wraps a `run_transaction` call that gets users in a particular city as a list of dictionaries.

        Arguments:
            city {String} -- The users' city.

        Returns:
            List -- A list of dictionaries containing user data.
        """
        return run_transaction(
            self.sessionmaker,
            lambda session: self._repo.get_objs(session, skip=skip, limit=limit),
        )

    async def get_user(
        self, phone_number: Optional[str] = None, user_id: Optional[UUID4] = None
    ):
        """
        Wraps a `run_transaction` call that gets a User object. As a required function for LoginManager, the function must take the `user_id` argument, and return a User object.

        Keyword Arguments:
            username {String} -- The user's username. (default: {None})
            user_id {UUID} -- The user's unique ID. (default: {None})

        Returns:
            User -- A User object.
        """
        with self.sessionmaker() as session:
            if user_id is not None:
                user = self._repo.get_obj(session, user_id)
            # if phone_number is not None:
            #     # check if user exists
            #     user = self._repo.get_user_txn(session, phone_number)

        return user
