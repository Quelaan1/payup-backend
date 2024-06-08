import logging

from payup_backend.app.cockroach_sql.dao.device_token_dao import DeviceTokenRepo
from payup_backend.app.modules.device_token.model import (
    DeviceTokenCreateRequest,
    DeviceTokenCreateResponse,
    DeviceTokenUpdateRequest,
    DeviceTokenUpdateResponse,
)
from ...cockroach_sql.database import database

logger = logging.getLogger(__name__)


class DeviceTokenService:
    """
    The class methods interact with multiple services to facilitate device token endpoints.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.sessionmaker = database.get_session()

        self._repo = DeviceTokenRepo()

    async def create_device_token(
        self, device_token: DeviceTokenCreateRequest
    ) -> DeviceTokenCreateResponse:
        """
        Wraps a `session` call that creates a device token.

        Arguments:
            device_token {DeviceTokenCreateRequest} -- The device token's creation request.
        """
        async with self.sessionmaker() as session:
            async with session.begin():
                await self._repo.create_device_token(
                    session=session, d_model=device_token
                )

                return DeviceTokenCreateResponse(
                    message="Device token created successfully"
                )

    async def update_device_token(
        self, device_token: DeviceTokenUpdateRequest
    ) -> DeviceTokenUpdateResponse:
        """
        Wraps a `session` call that updates a device token.

        Arguments:
            device_token {DeviceTokenUpdateRequest} -- The device token's update request.
        """
        async with self.sessionmaker() as session:
            async with session.begin():
                await self._repo.update_device_token(
                    session=session, d_model=device_token
                )

                return DeviceTokenUpdateResponse(
                    message="Device token updated successfully"
                )
