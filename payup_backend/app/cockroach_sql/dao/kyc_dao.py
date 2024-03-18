"""kyc_entity crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, Column

from ...modules.kyc.model import KycCreate, KycUpdate, Kyc as KycModel
from ..schemas import KycEntity as KycEntitySchema

logger = logging.getLogger(__name__)


class KycEntityRepo:
    """crud on kyc_entities model"""

    def __init__(self):
        self._schema = KycEntitySchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[KycModel]:
        """get kyc_entities list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get kyc_entity by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        return KycModel.model_validate(db_model)

    async def create_obj(self, session: AsyncSession, p_model: KycCreate) -> KycModel:
        """create kyc_entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = KycModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def update_obj(
        self, session: AsyncSession, obj_id: UUID, p_model: KycUpdate
    ) -> None:
        """update kyc_entity gives its primary key and update model"""
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        result = await session.execute(stmt)
        await session.flush()

        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    async def delete_obj(self, session: AsyncSession, obj_id: UUID) -> None:
        """deletes kyc_entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = await session.execute(stmt)
        await session.flush()
        logger.info("Rows updated: %s", result.rowcount)

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter kyc_entities table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]
