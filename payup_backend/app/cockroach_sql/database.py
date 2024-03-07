import logging

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from ..config.constants import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(name)s : %(message)s",
)
logger = logging.getLogger(__name__)


class Session:
    def __init__(self) -> None:
        self._session = None

    def __enter__(self):
        maker = sessionmaker(bind=database.engine)
        self._session = maker()
        return self._session

    def __exit__(self, type, value, traceback):
        self._session.close()


class PoolConnection:
    def __init__(self) -> None:
        self.connection = None

    def __enter__(self):
        eng: Engine = database.engine
        self.connection = eng.connect()
        return self  # Ensure this returns the PoolConnection instance

    def __exit__(self, type, value, traceback):
        self.connection.close()

    def execute(self, *args, **kwargs):
        return self.connection.execute(*args, **kwargs)


class Database(object):
    """
    Provides the database base functions.
    """

    def __init__(self):
        self._engine = None
        self._db = ""
        self._connection = None

    @property
    def engine(self):
        """
        Returns the database engine.
        """
        config = get_settings()

        if not self._engine:
            self._db = config.COCKROACH.DB
            conn_str = f"cockroachdb://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}?sslmode=verify-full"

            logger.info("database uri : %s", conn_str)
            self._engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                pool_recycle=1800,
                poolclass=QueuePool,
                pool_use_lifo=True,
                pool_size=5,
            )
            # self._engine = create_engine(
            #     "postgresql://{}".format(self._db),
            #     echo=False,
            #     poolclass=QueuePool,
            #     pool_size=2048,
            #     max_overflow=1024,
            #     client_encoding="utf8",
            # )
        return self._engine

    @property
    def get_connection(self):
        """
        Returns the database engine.
        """
        eng = self.engine
        return eng.connect()


database = Database()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()