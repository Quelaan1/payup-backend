"""profile crud to database"""

import logging
from uuid import UUID
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Column

from ...modules.profile.model import (
    ProfileCreate,
    ProfileUpdate,
    Profile as ProfileModel,
)
from ..schemas import Profile as ProfileSchema, User as UserSchema
from ...config.errors import DatabaseError
from ...config.errors import NotFoundError
from ...models.py_models import BaseResponse

logger = logging.getLogger(__name__)


class ProfileRepo:
    """crud on profiles model"""

    def __init__(self):
        self.repo_schema = ProfileSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[ProfileModel]:
        """get profiles list, paginated"""
        stmt = select(self.repo_schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [ProfileModel.model_validate(db_model) for db_model in db_models]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get profile by primary key"""
        stmt = select(self.repo_schema).filter(self.repo_schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model is None:
            return None
        return ProfileModel.model_validate(db_model)

    async def create_obj(
        self, session: AsyncSession, p_model: ProfileCreate
    ) -> ProfileModel:
        """create profile entity in db"""
        db_model = self.repo_schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = ProfileModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def update_obj(
        self,
        session: AsyncSession,
        obj_id: UUID,
        p_model: ProfileUpdate,
        col_filters: Optional[list[tuple[Column, Any]]] = None,
    ):
        """update profile gives its primary key and update model"""
        # db_model = session.get(self.repo_schema, obj_id)
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
        return ProfileModel.model_validate(db_model)

    async def delete_obj(self, session: AsyncSession, obj_id: UUID) -> None:
        """deletes profile entity from db"""
        stmt = delete(self.repo_schema).where(self.repo_schema.id == obj_id)
        result = session.execute(stmt)
        await session.flush()
        logger.info("Rows updated: %s", result.rowcount)

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter profile table for list"""
        stmt = select(self.repo_schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [ProfileModel.model_validate(db_model) for db_model in db_models]

    async def get_profile_by_user(self, session: AsyncSession, user_id: UUID):
        """
        Select a row of the profiles table, and return the row as a Profile object.

        Arguments:
            session {.Session} -- The active session for the database connection.

        Keyword Arguments:
            phone_number {String} -- The profile's phone_number. (default: {None})
            profile_id {UUID} -- The profile's unique ID. (default: {None})

        Returns:
            Profile -- A Profile object.
        """
        stmt = (
            select(self.repo_schema)
            .join_from(
                self.repo_schema,
                UserSchema,
                UserSchema.profile_id == self.repo_schema.id,
            )
            .where(UserSchema.id == user_id)
        )
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        if db_model:
            return ProfileModel.model_validate(db_model)
        raise DatabaseError(
            {"message": f"database inconsistence. no profile for user_id {user_id}"}
        )
