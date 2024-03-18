"""user crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, Column

from ...modules.user.model import UserCreate, UserUpdate, User as UserModel
from ..schemas import User as UserSchema


logger = logging.getLogger(__name__)


class UserRepo:
    """crud on users model"""

    def __init__(self):
        self._schema = UserSchema

    async def get_objs(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[UserModel]:
        """get users list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [UserModel.model_validate(db_model) for db_model in db_models]

    async def get_obj(self, session: AsyncSession, obj_id: UUID):
        """get user by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        result = await session.execute(stmt)
        db_model = result.scalars().first()
        return UserModel.model_validate(db_model)

    async def create_obj(self, session: AsyncSession, p_model: UserCreate) -> UserModel:
        """create user entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        await session.flush()
        await session.refresh(db_model)
        p_resp = UserModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def update_obj(
        self, session: AsyncSession, obj_id: UUID, p_model: UserUpdate
    ) -> None:
        """update user gives its primary key and update model"""
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
        """deletes user entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = await session.execute(stmt)
        await session.flush()
        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    async def get_obj_by_filter(
        self, session: AsyncSession, col_filters: list[tuple[Column, Any]]
    ):
        """filter user table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [UserModel.model_validate(db_model) for db_model in db_models]

    # def get_user_txn(self, session: AsyncSession, phone_number: str):
    #     """
    #     Select a row of the users table, and return the row as a User object.

    #     Arguments:
    #         session {.Session} -- The active session for the database connection.

    #     Keyword Arguments:
    #         phone_number {String} -- The user's phone_number. (default: {None})
    #         user_id {UUID} -- The user's unique ID. (default: {None})

    #     Returns:
    #         User -- A User object.
    #     """
    #     stmt = (
    #         select(self._schema)
    #         .join_from(
    #             self._schema,
    #             VerifierSchema,
    #             VerifierSchema.user_id == self._schema.id,
    #         )
    #         .where(VerifierSchema.phone_number == phone_number)
    #     )
    #     db_model = session.execute(stmt).scalars().first()
    #     return UserModel.model_validate(db_model) if db_model else None
