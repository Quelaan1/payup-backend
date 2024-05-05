"""otp crud to database"""

import logging
from uuid import UUID
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, Column

from ...modules.auth.model import OTPCreate, OTPUpdate, OTP as OTPModel
from ..schemas import OtpEntity as OTPSchema, PhoneEntity as PhoneSchema
from ...config.errors import NotFoundError
from ...config.constants import get_settings
from ...models.py_models import BaseResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

constants = get_settings()


class OTPRepo:
    """crud on otps model"""

    def __init__(self):
        self.repo_schema = OTPSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[OTPModel]:
        """get otps list, paginated"""
        stmt = select(self.repo_schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [OTPModel.model_validate(db_model) for db_model in db_models]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get otp by primary key"""
        stmt = select(self.repo_schema).filter(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model is None:
            return (
                None  # or you can raise an exception or return any other default value
            )
        return OTPModel.model_validate(db_model)

    async def create_obj(self, session: AsyncSession, p_model: OTPCreate) -> OTPModel:
        """create otp entity in db"""
        db_model = self.repo_schema(**p_model.model_dump(exclude=[""], by_alias=True))
        # db_model.attempt_remains = constants.TWILIO.MAX_SMS_ATTEMPTS - 1
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = OTPModel.model_validate(db_model)
        return p_resp

    async def update_obj(
        self,
        session: AsyncSession,
        obj_id: UUID,
        p_model: OTPUpdate,
        col_filters: Optional[list[tuple[Column, Any]]] = None,
    ):
        """update otp gives its primary key and update model"""
        stmt = select(self.repo_schema).where(self.repo_schema.id == obj_id)
        if not col_filters is None:
            for col, val in col_filters:
                stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model is None:
            raise NotFoundError(
                name=__name__, detail=BaseResponse(message=f"{__name__} not found")
            )

        update_data = p_model.model_dump(exclude=[""], exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_model, key, value)

        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        return OTPModel.model_validate(db_model)

    async def delete_obj(self, session: AsyncSession, obj_id: UUID) -> None:
        """deletes otp entity from db"""
        stmt = delete(self.repo_schema).where(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        await session.refresh()
        logger.info("Rows deleted: %s", result.rowcount)

    async def delete_obj_related_by_number(
        self,
        session: AsyncSession,
        phone_number: str,
        col_filters: list[tuple[Column, Any]],
    ):
        """Attempts to delete an otp entity from db and returns the deleted object if successful."""
        # Fetch and delete in a single transaction
        stmt = select(self.repo_schema)
        stmt = stmt.join_from(
            PhoneSchema,
            self.repo_schema,
            PhoneSchema.id == self.repo_schema.id,
        ).where(PhoneSchema.m_number == phone_number)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        obj_to_delete = await session.execute(stmt)
        db_model = obj_to_delete.scalars().first()

        if db_model is None:
            logger.info("Object not found with filters: %s", col_filters)
            return None  # Object not found, can't delete

        delete_stmt = delete(self.repo_schema)
        for col, val in col_filters:
            delete_stmt = delete_stmt.where(col == val)
        result = await session.execute(delete_stmt)
        await session.flush()
        logger.debug("Rows deleted: %s", result.rowcount)
        result.close()
        return OTPModel.model_validate(db_model)

    async def delete_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """Attempts to delete an otp entity from db and returns the deleted object if successful."""
        # Fetch and delete in a single transaction
        stmt = select(self.repo_schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        objs_to_delete = result.scalars().all()
        if objs_to_delete is None:
            logger.info("Object not found with filters: %s", col_filters)
            return None  # Object not found, can't delete

        delete_stmt = delete(self.repo_schema)
        for col, val in col_filters:
            delete_stmt = delete_stmt.where(col == val)
        result = await session.execute(delete_stmt)
        await session.flush()
        logger.info("Rows deleted: %s", result.rowcount)

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter otp table for list"""
        stmt = select(self.repo_schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [OTPModel.model_validate(db_model) for db_model in db_models]

    async def get_otp_by_phone(self, session: AsyncSession, phone_number: str):
        """filter otp table for list"""
        stmt = select(self.repo_schema)
        stmt = stmt.join_from(
            PhoneSchema,
            self.repo_schema,
            PhoneSchema.id == self.repo_schema.id,
        ).where(PhoneSchema.m_number == phone_number)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if not db_model is None:
            return OTPModel.model_validate(db_model)
        raise NotFoundError(name=__name__, detail="otp not found for this number")
