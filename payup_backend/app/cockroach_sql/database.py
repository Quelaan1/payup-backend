import logging
import tempfile
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from ..config.constants import get_settings
from ..helperClass.utils import set_db_cert

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

            if config.ENV == "local":
                # Write the certificate content to a temporary file
                data = set_db_cert()
                logger.info("cert_data: %s", data)
                cert_file_path = tempfile.mktemp(suffix=".crt")
                with open(cert_file_path, "w") as cert_file:
                    cert_file.write(data)
                conn_str = f"cockroachdb://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}?sslmode=verify-full&sslrootcert={cert_file_path}"
                # conn_str = f"cockroachdb://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}?sslmode=verify-full"

                self._engine = create_engine(
                    conn_str,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    poolclass=QueuePool,
                    pool_use_lifo=True,
                    pool_size=5,
                )
            elif config.ENV == "prod":

                # Write the certificate content to a temporary file
                cert_file_path = tempfile.mktemp(suffix=".crt")
                with open(cert_file_path, "w") as cert_file:
                    cert_file.write(config.COCKROACH.DB_CERT)
                conn_str = f"cockroachdb://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}?sslmode=verify-full&sslrootcert={cert_file_path}"

                self._engine = create_engine(
                    conn_str,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    poolclass=QueuePool,
                    pool_use_lifo=True,
                    pool_size=5,
                )
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
