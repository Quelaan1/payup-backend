import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete, update, Connection, Column

from ...modules.kyc.model import KycBase, KycCreate, KycUpdate, Kyc as KycModel
from ..schemas import pwd_context, KycEntity as KycEntitySchema
from ..db_enums import get_kyc_type_from_string

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class KycEntityRepo:

    def __init__(self):
        self._schema = KycEntitySchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[KycModel]:
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return KycModel.model_validate(db_model) if db_model else None

    def create_obj(self, session: Session, p_model: KycCreate) -> KycModel:
        # stmt = insert(KycSchema).values(**p_model.model_dump(), owner_id=user_id)
        db_model = self._schema(
            **p_model.model_dump()
            # ** p_model.model_dump(exclude=["entity_type"]),
            # entity_type=get_kyc_type_from_string(p_model.entity_type)
        )
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        p_resp = KycModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())

        return p_resp

    def update_obj(self, session: Session, obj_id: UUID, p_model: KycUpdate) -> None:
        stmt = (
            update(self._schema)
            .where(self._schema.id == obj_id)
            .values(**p_model.model_dump(exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        session.execute(stmt)

    def delete_obj(self, session: Session, obj_id: UUID) -> None:
        stmt = delete(self._schema).where(self._schema.id == obj_id)
        session.execute(stmt)

    def get_obj_by_filter(
        self, session: Session, cols: list[Column], col_vals: list[Any]
    ):
        stmt = select(self._schema)
        for i, col in enumerate(cols):
            stmt = stmt.filter(col == col_vals[i])
        db_models = session.execute(stmt).scalars().all()
        return [KycModel.model_validate(db_model) for db_model in db_models]
