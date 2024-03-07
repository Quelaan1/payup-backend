"""otp crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, Column

from ...modules.auth.model import OTPCreate, OTPUpdate, OTP as OTPModel
from ..schemas import OtpEntity as OTPSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class OTPRepo:
    """crud on otps model"""

    def __init__(self):
        self._schema = OTPSchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[OTPModel]:
        """get otps list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [OTPModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        """get otp by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return OTPModel.model_validate(db_model)

    def create_obj(self, session: Session, p_model: OTPCreate) -> OTPModel:
        """create otp entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.commit()
        session.refresh(db_model)
        p_resp = OTPModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    def update_obj(self, session: Session, obj_id: UUID, p_model: OTPUpdate) -> None:
        """update otp gives its primary key and update model"""
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude=[""], exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        result = session.execute(stmt)
        session.commit()

        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    def update_or_create_obj(self, session: Session, p_model: OTPCreate) -> OTPModel:
        """Create or update otp entity in db."""
        unique_identifier = (
            p_model.id
        )  # Replace `unique_field` with the actual field name used to identify uniqueness
        db_model = session.query(self._schema).filter_by(id=unique_identifier).first()

        if db_model:
            # The record exists, so update it
            logger.info("Updating existing db_model")
            for key, value in p_model.model_dump(exclude=["id"], by_alias=True).items():
                setattr(db_model, key, value)
        else:
            # The record does not exist, create a new one
            logger.info("Creating new db_model")
            db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
            session.add(db_model)

        session.commit()
        session.refresh(db_model)
        p_resp = OTPModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        """deletes otp entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = session.execute(stmt)
        session.commit()
        logger.info("Rows updated: %s", result.rowcount)

    def get_obj_by_filter(
        self, session: Session, col_filters: list[tuple[Column, Any]]
    ):
        """filter otp table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        db_models = session.execute(stmt).scalars().all()
        return [OTPModel.model_validate(db_model) for db_model in db_models]
