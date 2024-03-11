"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from pydantic import UUID4
from typing import Optional
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm import sessionmaker

from ...cockroach_sql.dao.user_dao import UserRepo
from .model import UserCreate
from ...cockroach_sql.database import database, PoolConnection

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
        self.connect = PoolConnection()

        self.sessionmaker = sessionmaker(bind=self.engine)
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


# if user is None:
#     # create user
#     user = self._repo.create_obj(
#         session=session, p_model=UserCreate(phone_number=phone_number)
#     )
# def start_ride(self, city, rider_id, vehicle_id):
#     """
#     Wraps a `run_transaction` call that starts a ride.

#     Arguments:
#         city {String} -- The ride's city.
#         rider_id {UUID} -- The user's unique ID.
#         vehicle_id {UUID} -- The vehicle's unique ID.
#     """

# def end_ride(self, ride_id, location):
#     """
#     Wraps a `run_transaction` call that ends a ride.

#     Arguments:
#         ride_id {UUID} -- The ride's unique ID.
#         location {String} -- The vehicle's last location.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: end_ride_txn(session, ride_id, location)
#     )

# def add_user(self, city, first_name, last_name, email, username, password):
#     """
#     Wraps a `run_transaction` call that adds a user.

#     Arguments:
#         city {String} -- The user's city.
#         first_name {String} -- The user's first name.
#         last_name {String} -- The user's last name.
#         email {String} -- The user's email.
#         username {String} -- The user's username.
#         password {String} -- The user's unhashed password.
#     """
#     return run_transaction(
#         self.sessionmaker,
#         lambda session: add_user_txn(
#             session, city, first_name, last_name, email, username, password
#         ),
#     )

# def remove_user(self, user_id):
#     """
#     Wraps a `run_transaction` call that "removes" a user. No rows are deleted by this function.

#     Arguments:
#         id {UUID} -- The user's unique ID.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: remove_user_txn(session, user_id)
#     )

# def remove_vehicle(self, vehicle_id):
#     """
#     Wraps a `run_transaction` call that "removes" a vehicle. No rows are deleted by this function.

#     Arguments:
#         id {UUID} -- The vehicle's unique ID.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: remove_vehicle_txn(session, vehicle_id)
#     )

# def add_vehicle(
#     self, city, owner_id, last_location, type, color, brand, status, is_owner=False
# ):
#     """
#     Wraps a `run_transaction` call that adds a vehicle.

#     Arguments:
#         city {String} -- The vehicle's city.
#         owner_id {UUID} -- The owner's unique ID.
#         last_location {String} -- The vehicle's location.
#         type {String} -- The vehicle's type.
#         color {String} -- The vehicle's color.
#         brand {String} -- The vehicle's brand.
#         status {String} -- The vehicle's availability.

#     Keyword Arguments:
#         is_owner {bool} -- The owner status of the user, before the vehicle is added. (default: {False})
#     """
#     return run_transaction(
#         self.sessionmaker,
#         lambda session: add_vehicle_txn(
#             session,
#             city,
#             owner_id,
#             last_location,
#             type,
#             color,
#             brand,
#             status,
#             is_owner,
#         ),
#     )

# def get_users(self, city):
#     """
#     Wraps a `run_transaction` call that gets users in a particular city as a list of dictionaries.

#     Arguments:
#         city {String} -- The users' city.

#     Returns:
#         List -- A list of dictionaries containing user data.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: get_users_txn(session, city)
#     )

# def get_vehicles(self, city):
#     """
#     Wraps a `run_transaction` call that gets vehicles in a particular city as a list of dictionaries.

#     Arguments:
#         city {String} -- The vehicle's city.

#     Returns:
#         List -- A list of dictionaries containing vehicle data.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: get_vehicles_txn(session, city)
#     )

# def get_rides(self, rider_id):
#     """
#     Wraps a `run_transaction` call that gets rides for a particular user as a list of dictionaries.

#     Arguments:
#         rider_id {UUID} -- The user's unique ID.

#     Returns:
#         List -- A list of dictionaries containing ride data.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: get_rides_txn(session, rider_id)
#     )
