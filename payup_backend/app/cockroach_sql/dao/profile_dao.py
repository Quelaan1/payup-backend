"""profile crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, Column

from ...modules.profile.model import (
    ProfileCreate,
    ProfileUpdate,
    Profile as ProfileModel,
)
from ..schemas import Profile as ProfileSchema, User as UserSchema
from ...config.errors import DatabaseError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class ProfileRepo:
    """crud on profiles model"""

    def __init__(self):
        self._schema = ProfileSchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[ProfileModel]:
        """get profiles list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [ProfileModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        """get profile by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return ProfileModel.model_validate(db_model)

    def create_obj(self, session: Session, p_model: ProfileCreate) -> ProfileModel:
        """create profile entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.commit()
        session.refresh(db_model)
        p_resp = ProfileModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    def update_obj(
        self, session: Session, obj_id: UUID, p_model: ProfileUpdate
    ) -> None:
        """update profile gives its primary key and update model"""
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        result = session.execute(stmt)
        session.commit()

        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        """deletes profile entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = session.execute(stmt)
        session.commit()
        logger.info("Rows updated: %s", result.rowcount)

    def get_obj_by_filter(
        self, session: Session, col_filters: list[tuple[Column, Any]]
    ):
        """filter profile table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        db_models = session.execute(stmt).scalars().all()
        return [ProfileModel.model_validate(db_model) for db_model in db_models]

    def get_profile_by_user(self, session: Session, user_id: UUID):
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
            select(self._schema)
            .join_from(
                self._schema,
                UserSchema,
                UserSchema.profile_id == self._schema.id,
            )
            .where(UserSchema.id == user_id)
        )
        db_model = session.execute(stmt).scalars().first()
        if db_model:
            return ProfileModel.model_validate(db_model)
        raise DatabaseError(
            {"message": f"database inconsistence. no profile for user_id {user_id}"}
        )
