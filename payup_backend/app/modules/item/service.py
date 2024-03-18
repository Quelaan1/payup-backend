"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID

from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.dialects import registry

from .dao import ItemRepo
from .model import ItemCreate
from ...cockroach_sql.database import database, PoolConnection

# to be called from router
# get pydantic-vallidated model for request-body as p_model parameter.
# call dao functions inside a connection context
# return response data pydantic model or exception


# registry.register("cockroachdb", "cockroachdb.sqlalchemy.dialect", "CockroachDBDialect")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class ItemService:
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

        self.sessionmaker = sessionmaker(bind=self.connect)
        self.item_repo = ItemRepo()

    def create_item(self, req_body: ItemCreate, user_id: UUID):
        """
        Wraps a `run_transaction` call that creates an item.

        Arguments:
            reqBody {ItemCreate} -- The item's validated pydantic request model.
            user_id {UUID} -- The user's unique ID.
        """
        return run_transaction(
            self.sessionmaker,
            lambda session: self.item_repo.create_obj(
                p_model=req_body, session=session, user_id=user_id
            ),
        )

    def get_items(self, skip, limit):
        """
        Wraps a `run_transaction` call that gets users in a particular city as a list of dictionaries.

        Arguments:
            city {String} -- The users' city.

        Returns:
            List -- A list of dictionaries containing user data.
        """
        return run_transaction(
            self.sessionmaker,
            lambda session: self.item_repo.get_objs(session, skip=skip, limit=limit),
        )
