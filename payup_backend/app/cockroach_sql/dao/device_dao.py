import datetime
import logging
from uuid import UUID
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Column
from payup_backend.app.cockroach_sql.schemas import DeviceSchema
from payup_backend.app.config.errors import NotFoundError
from payup_backend.app.modules.device.model import (
    Device as DeviceModel,
    DeviceRegistrationRequest,
)


logger = logging.getLogger(__name__)


class DeviceRepo:
    """crud on devices model"""

    def __init__(self):
        self.repo_schema = DeviceSchema

    async def get_devices(
        self, session: AsyncSession, user_id: UUID
    ) -> list[DeviceModel]:
        """get devices list for a user"""
        stmt = select(self.repo_schema).filter(self.repo_schema.user_id == user_id)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [DeviceModel.model_validate(db_model) for db_model in db_models]

    async def get_device(self, session: AsyncSession, device_id: UUID):
        """get device by device id"""
        stmt = select(self.repo_schema).filter(self.repo_schema.device_id == device_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model is None:
            return None
        return DeviceModel.model_validate(db_model)

    async def create_device(
        self, session: AsyncSession, d_model: DeviceRegistrationRequest
    ) -> DeviceModel:
        """create device entity in db"""
        db_model = self.repo_schema(**d_model.model_dump(exclude=[""], by_alias=True))  # type: ignore
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        d_resp = DeviceModel.model_validate(db_model)
        logger.info("[response]-[%s]", d_resp.model_dump())
        return d_resp

    async def update_last_used(
        self,
        session: AsyncSession,
        device_id: UUID,
        user_id: UUID,
    ):
        """Update the last_used field of a device given its primary key."""
        stmt = select(self.repo_schema).where(
            self.repo_schema.device_id == device_id, self.repo_schema.user_id == user_id
        )

        result = await session.execute(stmt)
        db_model = result.scalars().first()

        if db_model is None:
            raise NotFoundError(
                name="Device Not Found",
                detail=f"Device with id {device_id} for {user_id} not found",
            )

        db_model.last_used = datetime.datetime.now(pytz.UTC).replace(tzinfo=None)  # type: ignore
        db_model.updated_at = datetime.datetime.now(pytz.UTC).replace(tzinfo=None)  # type: ignore

        session.add(db_model)
        await session.commit()

    async def delete_device_for_all_users(self, session: AsyncSession, device_id: UUID):
        """Delete a device for all users."""
        stmt = delete(self.repo_schema).where(self.repo_schema.device_id == device_id)
        result = await session.execute(stmt)
        await session.flush()
        return result

    async def delete_device_for_user(
        self, session: AsyncSession, device_id: UUID, user_id: UUID
    ):
        """Delete a device for a user."""
        stmt = delete(self.repo_schema).where(
            self.repo_schema.device_id == device_id, self.repo_schema.user_id == user_id
        )
        result = await session.execute(stmt)
        await session.flush()
        return result
