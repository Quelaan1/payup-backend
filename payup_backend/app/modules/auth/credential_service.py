"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from typing import Optional
from pydantic import UUID4
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm import sessionmaker

from ...cockroach_sql.dao.verifier_dao import VerifierRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from .model import VerifierCreate
from ...cockroach_sql.database import database, PoolConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class VerifierService:
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
        # self.connect = self.engine.connect()
        self.connect = PoolConnection()

        self.sessionmaker = sessionmaker(bind=self.engine)
        self._repo = VerifierRepo()
        self.user_repo = UserRepo()

    async def create_credential(self, req_body: VerifierCreate):
        """
        Wraps a `run_transaction` call that creates an credential.

        Arguments:
            reqBody {VerifierCreate} -- The credential's validated pydantic request model.
        """

        with self.sessionmaker() as session:
            return self._repo.create_obj(p_model=req_body, session=session)

    async def get_credential(
        self, phone_number: Optional[str] = None, user_id: Optional[UUID4] = None
    ):
        """
        Wraps a `run_transaction` call that gets a Verifier object. As a required function for LoginManager, the function must take the `credential_id` argument, and return a Verifier object.

        Keyword Arguments:
            phone_number {String} -- The user's phone number.

        Returns:
            Verifier -- A Verifier object.
        """
        with self.sessionmaker() as session:
            if user_id is not None:
                credential = self._repo.get_obj_by_filter(
                    session, cols=["user_id"], col_vals=[user_id]
                )
                return credential[0]
            if phone_number is not None:
                credential = self._repo.get_obj_by_phone_number(
                    session=session, phone_number=phone_number
                )
                return credential
            raise ValueError(
                "atleast one of the arguments phone_number, user_id is required"
            )


# if credential is None:
#     # create credential
#     credential = self._repo.create_obj(
#         session=session, p_model=VerifierCreate(phone_number=phone_number)
#     )
# def start_ride(self, city, rider_id, vehicle_id):
#     """
#     Wraps a `run_transaction` call that starts a ride.

#     Arguments:
#         city {String} -- The ride's city.
#         rider_id {UUID} -- The credential's unique ID.
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

# def add_credential(self, city, first_name, last_name, email, credentialname, password):
#     """
#     Wraps a `run_transaction` call that adds a credential.

#     Arguments:
#         city {String} -- The credential's city.
#         first_name {String} -- The credential's first name.
#         last_name {String} -- The credential's last name.
#         email {String} -- The credential's email.
#         credentialname {String} -- The credential's credentialname.
#         password {String} -- The credential's unhashed password.
#     """
#     return run_transaction(
#         self.sessionmaker,
#         lambda session: add_credential_txn(
#             session, city, first_name, last_name, email, credentialname, password
#         ),
#     )

# def remove_credential(self, credential_id):
#     """
#     Wraps a `run_transaction` call that "removes" a credential. No rows are deleted by this function.

#     Arguments:
#         id {UUID} -- The credential's unique ID.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: remove_credential_txn(session, credential_id)
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
#         is_owner {bool} -- The owner status of the credential, before the vehicle is added. (default: {False})
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

# def get_credentials(self, city):
#     """
#     Wraps a `run_transaction` call that gets credentials in a particular city as a list of dictionaries.

#     Arguments:
#         city {String} -- The credentials' city.

#     Returns:
#         List -- A list of dictionaries containing credential data.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: get_credentials_txn(session, city)
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
#     Wraps a `run_transaction` call that gets rides for a particular credential as a list of dictionaries.

#     Arguments:
#         rider_id {UUID} -- The credential's unique ID.

#     Returns:
#         List -- A list of dictionaries containing ride data.
#     """
#     return run_transaction(
#         self.sessionmaker, lambda session: get_rides_txn(session, rider_id)
#     )
