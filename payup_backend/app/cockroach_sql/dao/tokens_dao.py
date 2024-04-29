"""refresh_token_entity crud to database"""

import logging
from uuid import UUID
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Column
from sqlalchemy.dialects import postgresql

from ...modules.token.model import (
    RefreshTokenCreate,
    RefreshTokenUpdate,
    RefreshToken as RefreshTokenModel,
    AccessTokenBlacklistCreate,
    AccessTokenBlacklist as AccessTokenBlacklistModel,
)
from ..schemas import (
    RefreshTokenEntity as RefreshTokenSchema,
    AccessTokenBlacklist as AccessTokenBlacklistSchema,
    User as UserSchema,
)
from ...config.errors import NotFoundError
from ...models.py_models import BaseResponse


logger = logging.getLogger(__name__)


class RefreshTokenRepo:
    """crud on refresh_token_entities model"""

    def __init__(self):
        self.repo_schema = RefreshTokenSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[RefreshTokenModel]:
        """get refresh_token_entities list, paginated"""
        stmt = select(self.repo_schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [RefreshTokenModel.model_validate(db_model) for db_model in db_models]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get refresh_token_entitie by primary key"""
        stmt = select(self.repo_schema).filter(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        return RefreshTokenModel.model_validate(db_model)

    async def create_obj(
        self, session: AsyncSession, p_model: RefreshTokenCreate
    ) -> RefreshTokenModel:
        """create refresh_token_entitie entity in db"""
        db_model = self.repo_schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = RefreshTokenModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def update_obj(
        self,
        session: AsyncSession,
        obj_id: UUID,
        p_model: RefreshTokenUpdate,
        col_filters: Optional[list[tuple[Column, Any]]] = None,
    ):
        """update refresh_token given its primary key and update model"""
        # db_model = session.get(self.repo_schema, obj_id)
        stmt = select(self.repo_schema).where(self.repo_schema.id == obj_id)
        if col_filters is not None:
            for col, val in col_filters:
                stmt = stmt.where(col == val)
        # Compile the statement to a string of raw SQL
        compiled_stmt = stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )

        # Log the raw SQL statement
        logger.debug(compiled_stmt)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model is None:
            raise NotFoundError(
                name=__name__, detail=BaseResponse(detail="RefreshToken not found")
            )

        update_data = p_model.model_dump(exclude=[""], exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_model, key, value)

        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)

        logger.debug("RefreshToken updated: %s", db_model.id)
        return db_model

    async def update_or_create_obj(
        self, session: AsyncSession, p_model: RefreshTokenCreate
    ) -> RefreshTokenModel:
        """Create or update refresh_token_entitie entity in db."""
        unique_identifier = (
            p_model.id
        )  # Replace `unique_field` with the actual field name used to identify uniqueness
        result = await session.execute(
            select(self.repo_schema).filter_by(id=unique_identifier)
        )
        db_model = result.scalars().first()

        if db_model:
            for key, value in p_model.model_dump(exclude=["id"], by_alias=True).items():
                setattr(db_model, key, value)
        else:
            db_model = self.repo_schema(
                **p_model.model_dump(exclude=[""], by_alias=True)
            )
            session.add(db_model)

        await session.flush()
        await session.refresh(db_model)
        p_resp = RefreshTokenModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def delete_obj(self, session: AsyncSession, obj_id: UUID) -> None:
        """deletes refresh_token_entitie entity from db"""
        stmt = delete(self.repo_schema).where(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        await session.refresh()
        logger.info("Rows deleted: %s", result.rowcount)
        result.close()

    async def delete_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """Attempts to delete an refresh_token_entitie entity from db and returns the deleted object if successful."""
        # Build a delete statement based on the same filters
        delete_stmt = delete(self.repo_schema)
        for col, val in col_filters:
            delete_stmt = delete_stmt.where(col == val)

        # Execute the delete operation and get the result
        result = await session.execute(delete_stmt)
        logger.info("Rows deleted: %s", result.rowcount)
        result.close()

    async def delete_obj_related_by_profile(
        self,
        session: AsyncSession,
        profile_id: UUID,
        col_filters: Optional[list[tuple[Column, Any]]] = None,
    ):
        """Attempts to delete an otp entity from db and returns the deleted object if successful."""
        # Fetch and delete in a single transaction
        # Build a delete statement
        delete_stmt = delete(self.repo_schema).where(
            self.repo_schema.user_id.in_(
                select(UserSchema.id).where(UserSchema.profile_id == profile_id)
            )
        )

        if col_filters:
            for col, val in col_filters:
                delete_stmt = delete_stmt.where(col == val)

        # Execute the delete statement in a single call
        result = await session.execute(delete_stmt)
        logger.debug("Deleted %s rows.", result.rowcount)
        result.close()

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter refresh_token_entitie table for list"""
        stmt = select(self.repo_schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [RefreshTokenModel.model_validate(db_model) for db_model in db_models]


class AccessTokenBlacklistRepo:
    """crud on access_token_blacklists model"""

    def __init__(self):
        self.repo_schema = AccessTokenBlacklistSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[AccessTokenBlacklistModel]:
        """get access_token_blacklists list, paginated"""
        stmt = select(self.repo_schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [
            AccessTokenBlacklistModel.model_validate(db_model) for db_model in db_models
        ]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get access_token_blacklist by primary key"""
        stmt = select(self.repo_schema).filter(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        return AccessTokenBlacklistModel.model_validate(db_model)

    async def create_obj(
        self, session: AsyncSession, p_model: AccessTokenBlacklistCreate
    ) -> AccessTokenBlacklistModel:
        """create access_token_blacklist entity in db"""
        db_model = self.repo_schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = AccessTokenBlacklistModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp
