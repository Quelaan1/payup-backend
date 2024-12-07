import logging
from uuid import UUID
from fastapi import HTTPException, status

from payup_backend.app.cockroach_sql.dao.device_dao import DeviceRepo
from payup_backend.app.modules.device.model import (
    DeviceListResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
)
from ...cockroach_sql.database import database

logger = logging.getLogger(__name__)


class DeviceService:
    """
    The class methods interact with multiple services to facilitate device endpoints.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.sessionmaker = database.get_session()

        self._repo = DeviceRepo()

    async def register_device(
        self, device: DeviceRegistrationRequest, user_id: UUID
    ) -> DeviceRegistrationResponse:
        """
        Wraps a `session` call that registers a device.

        Arguments:
            device {DeviceRegistrationRequest} -- The device's registration request.
        """
        try:
            # First transaction to commit the deletion
            async with self.sessionmaker() as session:
                async with session.begin():
                    await self._repo.delete_device_for_all_users(
                        session=session, device_id=device.device_id
                    )

                    await session.commit()

            # Second transaction for the rest of the operations
            async with self.sessionmaker() as session:
                async with session.begin():
                    user_devices = await self._repo.get_devices(
                        session=session, user_id=user_id
                    )

                    if len(user_devices) >= 2:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User already has 2 devices registered",
                        )

                    device.user_id = user_id

                    await self._repo.create_device(
                        session=session,
                        d_model=device,
                    )

                    await session.commit()

            return DeviceRegistrationResponse(message="Device registered successfully")
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            detail_message = (
                err.args[0] if err.args else "An unexpected error occurred."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail_message
            ) from err

    async def get_user_devices(self, user_id: UUID) -> DeviceListResponse:
        """
        Wraps a `session` call that gets a list of devices for a user.

        Arguments:
            user_id {UUID} -- The user's unique ID.
        """
        try:
            async with self.sessionmaker() as session:
                devices = await self._repo.get_devices(session=session, user_id=user_id)

                if not devices:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No devices found",
                    )

                await session.commit()
            return DeviceListResponse(Devices=devices)
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err

    async def delete_device(
        self, device_id: str, user_id: UUID
    ) -> DeviceRegistrationResponse:
        """
        Wraps a `session` call that deletes a device.

        Arguments:
            device {DeviceDeleteRequest} -- The device's delete request.
        """
        try:
            async with self.sessionmaker() as session:
                device = await self._repo.delete_device_for_user(
                    session=session, device_id=device_id, user_id=user_id
                )

                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No device found",
                    )
                await session.commit()

            return DeviceRegistrationResponse(message="Device deleted successfully")
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err

    async def delete_user_devices(self, user_id: UUID) -> DeviceRegistrationResponse:
        """
        Wraps a `session` call that deletes all devices for a user.

        Arguments:
            user_id {UUID} -- The user's unique ID.
        """
        try:
            async with self.sessionmaker() as session:
                await self._repo.delete_devices_for_user(
                    session=session, user_id=user_id
                )
                await session.commit()

            return DeviceRegistrationResponse(
                message="All devices deleted successfully"
            )
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err

    async def update_last_used(
        self, device_id: str, user_id: UUID
    ) -> DeviceRegistrationResponse:
        """
        Wraps a `session` call that updates the last used field of a device.

        Arguments:
            device_id {UUID} -- The device's unique ID.
            user_id {UUID} -- The user's unique ID.
        """
        try:
            async with self.sessionmaker() as session:
                await self._repo.update_last_used(
                    session=session, device_id=device_id, user_id=user_id
                )
                await session.commit()

                return DeviceRegistrationResponse(
                    message="Device last used updated successfully"
                )
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err
