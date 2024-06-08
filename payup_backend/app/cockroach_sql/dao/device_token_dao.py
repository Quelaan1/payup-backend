from datetime import datetime
import logging
from uuid import UUID
import pytz
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from payup_backend.app.cockroach_sql.schemas import DeviceTokenSchema
from payup_backend.app.config.errors import NotFoundError
from payup_backend.app.modules.device_token.model import (
    DeviceToken as DeviceTokenModel,
    DeviceTokenCreateRequest,
    DeviceTokenUpdateRequest,
)


logger = logging.getLogger(__name__)


class DeviceTokenRepo:
    """CRUD operations on device tokens model"""

    def __init__(self):
        self.repo_schema = DeviceTokenSchema

    async def get_device_tokens(
        self, session: AsyncSession, device_id: UUID
    ) -> list[DeviceTokenModel]:
        """Get device tokens for a device"""
        stmt = select(self.repo_schema).filter(self.repo_schema.device_id == device_id)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [DeviceTokenModel.model_validate(db_model) for db_model in db_models]

    async def create_device_token(
        self, session: AsyncSession, d_model: DeviceTokenCreateRequest
    ) -> DeviceTokenModel:
        """Create device token entity in db"""
        db_model = self.repo_schema(**d_model.model_dump(exclude=[""], by_alias=True))  # type: ignore
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        d_resp = DeviceTokenModel.model_validate(db_model)
        logger.info("[response]-[%s]", d_resp.model_dump())
        return d_resp

    async def update_device_token(
        self,
        session: AsyncSession,
        d_model: DeviceTokenUpdateRequest,
    ):
        """Update a device token"""
        stmt = select(self.repo_schema).where(
            self.repo_schema.token_purpose == d_model.token_purpose,
            self.repo_schema.device_id == d_model.device_id,
        )

        result = await session.execute(stmt)
        db_model = result.scalars().first()

        if db_model is None:
            raise NotFoundError(
                name="DeviceToken Not Found",
                detail=f"DeviceToken for purpose {d_model.token_purpose} not found for device {d_model.device_id}",
            )

        for key, value in d_model.model_dump(
            exclude=["token_id"], by_alias=True  # type: ignore
        ).items():
            setattr(db_model, key, value)

        db_model.updated_at = datetime.now(pytz.UTC).replace(tzinfo=None)  # type: ignore

        session.add(db_model)
        await session.commit()

    async def delete_tokens_for_device(self, session: AsyncSession, device_id: UUID):
        """Delete all tokens for a device"""
        stmt = delete(self.repo_schema).where(self.repo_schema.device_id == device_id)
        result = await session.execute(stmt)
        await session.flush()
        return result
