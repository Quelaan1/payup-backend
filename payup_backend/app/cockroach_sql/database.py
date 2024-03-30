import os
import logging
import tempfile
import ssl

# from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool

from ..config.constants import get_settings
from ..helperClass.utils import get_db_cert

logger = logging.getLogger(__name__)


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

        if self._engine is None:
            self._db = config.COCKROACH.DB
            conn_str = f"cockroachdb+asyncpg://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}?sslmode=verify-full"
            base_conn_str = f"cockroachdb+asyncpg://{config.COCKROACH.USER}:{config.COCKROACH.PASSWORD}@{config.COCKROACH.DB_URI}/{config.COCKROACH.DB}"

            if config.ENV == "local":
                # Set up the SSL context
                appdata = os.getenv("APPDATA")
                ssl_context = ssl.create_default_context(
                    cafile=f"{appdata}/postgresql/root.crt"
                )
                ssl_context.check_hostname = (
                    False  # Adjust based on your SSL config needs
                )
                ssl_context.verify_mode = ssl.CERT_REQUIRED

                # Append asyncpg-specific SSL parameters to the connection string
                conn_str = f"{base_conn_str}?ssl=true"
                self._engine = create_async_engine(
                    conn_str,
                    connect_args={"ssl": ssl_context},
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    pool_size=5,
                )
            elif config.ENV == "prod":

                # Write the certificate content to a temporary file
                cert_file_path = tempfile.mktemp(suffix=".crt")
                with open(cert_file_path, "w") as cert_file:
                    cert_file.write(get_db_cert())

                conn_str = conn_str + f"&sslrootcert={cert_file_path}"

                self._engine = create_async_engine(
                    conn_str,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    pool_use_lifo=True,
                    pool_size=5,
                )
            else:
                raise ValueError("environment value can be either local or prod")
        return self._engine

    async def get_session(self) -> AsyncSession:
        async_engine = await self.engine
        async_session = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session()


database = Database()


# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)


# class Session:
#     def __init__(self) -> None:
#         self._session = None

#     def __enter__(self):
#         maker = sessionmaker(bind=database.engine)
#         self._session = maker()
#         return self._session

#     def __exit__(self, type, value, traceback):
#         self._session.close()


# class PoolConnection:
#     def __init__(self) -> None:
#         self.connection = None

#     def __enter__(self):
#         eng: Engine = database.engine
#         self.connection = eng.connect()
#         return self  # Ensure this returns the PoolConnection instance

#     def __exit__(self, type, value, traceback):
#         self.connection.close()

#     def execute(self, *args, **kwargs):
#         return self.connection.execute(*args, **kwargs)


# def get_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
