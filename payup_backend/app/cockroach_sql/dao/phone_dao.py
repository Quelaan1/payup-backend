"""phone crud to database"""

import logging
from uuid import UUID
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, Column
from sqlalchemy.dialects import postgresql

from ...modules.phone.model import PhoneCreate, PhoneUpdate, Phone as PhoneModel
from ..schemas import PhoneEntity as PhoneSchema
from ...config.errors import NotFoundError
from ...models.py_models import BaseResponse

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
        logger.debug("db_model : %s", db_model)
        session.add(db_model)
        session.flush()
        session.refresh(db_model)
        p_resp = PhoneModel.model_validate(db_model)
        logger.debug("[response]-[%s]", p_resp.model_dump())
        return p_resp

    async def update_obj(
        self,
        session: Session,
        obj_id: UUID,
        p_model: PhoneUpdate,
        col_filters: Optional[list[tuple[Column, Any]]] = None,
    ):
        """update phone given its primary key and update model"""
        # db_model = session.get(self._schema, obj_id)
        stmt = select(self._schema).where(self._schema.id == obj_id)
        if col_filters is not None:
            for col, val in col_filters:
                stmt = stmt.where(col == val)
        # Compile the statement to a string of raw SQL
        compiled_stmt = stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )

        # Log the raw SQL statement
        logger.debug(compiled_stmt)
        db_model = session.execute(stmt).scalars().first()
        if db_model is None:
            raise NotFoundError(
                name=__name__, detail=BaseResponse(detail="Phone not found")
            )

        update_data = p_model.model_dump(exclude=["m_pin"], exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_model, key, value)

        if p_model.m_pin is not None:
            db_model.pin = self._schema.get_hash_password(
                p_model.m_pin.get_secret_value()
            )

        session.add(db_model)
        session.flush()
        session.refresh(db_model)

        logger.debug("Phone updated: %s", db_model.id)
        return db_model

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        """deletes phone entity from db"""
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        result = session.execute(stmt)
        session.flush()
        logger.info("Rows updated: %s", result.rowcount)

    def get_obj_by_filter(
        self, session: Session, col_filters: list[tuple[Column, Any]]
    ):
        """filter phone table for list"""
        stmt = select(self._schema)
        for col, val in col_filters:
            stmt = stmt.where(col == val)
        # Compile the statement to a string of raw SQL
        compiled_stmt = stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )

        # Log the raw SQL statement
        logger.info(compiled_stmt)
        db_models = session.execute(stmt).scalars().all()
        return [PhoneModel.model_validate(db_model) for db_model in db_models]
