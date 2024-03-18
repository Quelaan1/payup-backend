"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging

from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status
from ...cockroach_sql.database import database
from ...config.constants import get_settings
from .pan.pan_model import PANVerifyResponseSchema

# from ...dependency import authentication


logger = logging.getLogger(__name__)

constants = get_settings()


class KycService:
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
        self.sessionmaker = sessionmaker(bind=self.engine)

    async def verify_kyc(self, kyc_entity: str):
        """validate an access token"""
        try:
            logger.debug("kyc entity passed : %s", kyc_entity)

            return PANVerifyResponseSchema(message="True")

        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args,
            ) from err
