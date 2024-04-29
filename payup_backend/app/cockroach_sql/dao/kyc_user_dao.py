"""kyc_entity crud to database"""

import logging
from uuid import UUID
from typing import Any, Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Column, or_, and_

from ...modules.kyc.model import UserKycRelationBase as RelationModel
from ..schemas import UserKycRelation as UserKycRelationSchema

logger = logging.getLogger(__name__)


class UserKycRelationRepo:
    """crud on kyc_entities model"""

    def __init__(self):
        self.repo_schema = UserKycRelationSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[RelationModel]:
        """get kyc_entities list, paginated"""
        stmt = select(self.repo_schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [RelationModel.model_validate(db_model) for db_model in db_models]

    async def get_by_related_obj(
        self, session: AsyncSession, user_id: Optional[UUID], kyc_id: Optional[UUID]
    ):
        """get kyc_entity by primary key"""
        stmt = select(self.repo_schema)
        if not user_id is None:
            stmt = stmt.filter(self.repo_schema.user_id == user_id)
        if not kyc_id is None:
            stmt = stmt.filter(self.repo_schema.kyc_id == kyc_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        return RelationModel.model_validate(db_model)

    async def create_obj(
        self, session: AsyncSession, user_id: UUID, kyc_id: UUID
    ) -> RelationModel:
        """create kyc_entity in db"""
        try:
            db_model = self.repo_schema(user_id=user_id, kyc_id=kyc_id)
            logger.info("db_model : %s", db_model)
            session.add(db_model)
            await session.flush()
            await session.refresh(db_model)
            p_resp = RelationModel.model_validate(db_model)
            logger.info("[response]-[%s]", p_resp.model_dump())
            return p_resp
        except Exception as e:
            logger.error("%s", e)
            raise e

    async def get_or_create_obj(
        self, session: AsyncSession, user_id: UUID, kyc_id: UUID
    ) -> RelationModel:
        """Get or create a KYC entity in db."""

        stmt = (
            select(self.repo_schema)
            .where(self.repo_schema.kyc_id == kyc_id)
            .where(self.repo_schema.user_id == user_id)
        )
        result = await session.execute(stmt)
        db_model = result.scalars().first()

        if db_model is None:
            # The record does not exist, create a new one
            return await self.create_obj(
                session=session, kyc_id=kyc_id, user_id=user_id
            )

        p_resp = RelationModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def delete_obj(
        self,
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        kyc_id: Optional[UUID] = None,
        cond: Optional[Literal["OR", "AND"]] = None,
    ) -> None:
        """deletes kyc_entity from db"""
        stmt = delete(self.repo_schema)

        if user_id is not None and kyc_id is not None:
            if cond == "OR":
                stmt = stmt.where(
                    or_(
                        self.repo_schema.user_id == user_id,
                        self.repo_schema.kyc_id == kyc_id,
                    )
                )
            elif cond == "AND":
                stmt = stmt.where(
                    and_(
                        self.repo_schema.user_id == user_id,
                        self.repo_schema.kyc_id == kyc_id,
                    )
                )
            else:
                # Default behavior if cond is not specified but both IDs are provided
                stmt = stmt.where(self.repo_schema.user_id == user_id).where(
                    self.repo_schema.kyc_id == kyc_id
                )
        elif user_id is not None:
            stmt = stmt.where(self.repo_schema.user_id == user_id)
        elif kyc_id is not None:
            stmt = stmt.where(self.repo_schema.kyc_id == kyc_id)
        result = await session.execute(stmt)
        await session.flush()
        logger.info("Rows updated: %s", result.rowcount)

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter kyc_entities table for list"""
        stmt = select(self.repo_schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [RelationModel.model_validate(db_model) for db_model in db_models]
