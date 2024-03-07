"""phone crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, Column

from ...modules.phone.model import PhoneCreate, PhoneUpdate, Phone as PhoneModel
from ..schemas import PhoneEntity as PhoneSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class PhoneRepo:
    """crud on phones model"""

    def __init__(self):
        self._schema = PhoneSchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[PhoneModel]:
        """get phones list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        """get phone by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return PhoneModel.model_validate(db_model)

    def create_obj(self, session: Session, p_model: PhoneCreate) -> PhoneModel:
        """create phone entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=["m_pin"], by_alias=True))
        if p_model.m_pin is not None:
            db_model.set_password(p_model.m_pin.get_secret_value())
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.commit()
        session.refresh(db_model)
        p_resp = PhoneModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    def update_obj(self, session: Session, obj_id: UUID, p_model: PhoneUpdate) -> None:
        """update phone gives its primary key and update model"""
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude=["m_pin"], exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        if p_model.m_pin is not None:
            stmt = stmt.values(
                {
                    "pin": self._schema.get_hash_password(
                        p_model.m_pin.get_secret_value()
                    )
                }
            )
        result = session.execute(stmt)
        session.commit()

        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        """deletes phone entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = session.execute(stmt)
        session.commit()
        logger.info("Rows updated: %s", result.rowcount)

    def get_obj_by_filter(
        self, session: Session, col_filters: list[tuple[Column, Any]]
    ):
        """filter phone table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        db_models = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(db_model) for db_model in db_models]
