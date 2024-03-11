"""kyc_entity crud to database"""

import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, Column

from ...modules.kyc.model import KycCreate, KycUpdate, Kyc as KycModel
from ..schemas import KycEntity as KycEntitySchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class KycEntityRepo:
    """crud on kyc_entities model"""

    def __init__(self):
        self._schema = KycEntitySchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[KycModel]:
        """get kyc_entities list, paginated"""
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        """get kyc_entity by primary key"""
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return KycModel.model_validate(db_model)

    def create_obj(self, session: Session, p_model: KycCreate) -> KycModel:
        """create kyc_entity in db"""
        db_model = self._schema(**p_model.model_dump(exclude=[""], by_alias=True))
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.flush()
        session.refresh(db_model)
        p_resp = KycModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())
        return p_resp

    def update_obj(self, session: Session, obj_id: UUID, p_model: KycUpdate) -> None:
        """update kyc_entity gives its primary key and update model"""
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        result = session.execute(stmt)
        session.flush()

        logger.info("Rows updated: %s", result.rowcount)
        result.close()

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        """deletes kyc_entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = session.execute(stmt)
        session.flush()
        logger.info("Rows updated: %s", result.rowcount)

    def get_obj_by_filter(
        self, session: Session, col_filters: list[tuple[Column, Any]]
    ):
        """filter kyc_entities table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        db_models = session.execute(stmt).scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]
