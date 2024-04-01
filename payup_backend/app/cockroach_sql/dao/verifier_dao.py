# import logging
# from uuid import UUID
# from typing import Any, Union
# from sqlalchemy.orm import Session
# from sqlalchemy import select, delete, update, Column

# from ...modules.auth.model import (
#     VerifierCreate,
#     VerifierUpdate,
#     Verifier as VerifierModel,
# )
# from ..schemas import Verifier as VerifierSchema, User as UserSchema
# from ...config.errors import DatabaseError

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
# )
# logger = logging.getLogger(__name__)


# class VerifierRepo:

#     def __init__(self):
#         self.repo_schema = VerifierSchema
#         self._model = VerifierModel

#     def get_objs(self, session: Session, skip: int = 0, limit: int = 100):
#         stmt = select(self.repo_schema).offset(skip).limit(limit)
#         db_models = session.execute(stmt).scalars().all()
#         return [self._model.model_validate(db_model) for db_model in db_models]

#     def get_obj(self, session: Session, obj_id: UUID):
#         stmt = select(self.repo_schema).filter(self.repo_schema.id == obj_id)
#         db_model = session.execute(stmt).scalars().first()
#         return self._model.model_validate(db_model)

#     def get_obj_by_phone_number(self, session: Session, phone_number: str):
#         stmt = (
#             select(self.repo_schema).filter(self.repo_schema.phone_number == phone_number)
#             # select(self.repo_schema)
#             # .join(UserSchema, UserSchema.id == VerifierSchema.user_id)
#             # .where(UserSchema.phone_number == phone_number)
#         )

#         # Execute the query and fetch the first result
#         db_model = session.execute(stmt).scalars().first()

#         if db_model is not None:
#             return self._model.model_validate(db_model)
#         raise DatabaseError({"details": "record not found"})

#     def create_obj(self, session: Session, p_model: VerifierCreate):

#         db_model = self.repo_schema(**p_model.model_dump(exclude=["m_pin"]))
#         if p_model.m_pin is not None:
#             db_model.set_password(p_model.m_pin.get_secret_value())

#         logger.info("db_model : %s", db_model)
#         session.add(db_model)
#         session.commit()
#         session.refresh(db_model)

#         p_resp = self._model.model_validate(db_model)
#         logger.info("[response]-[%s]", p_resp.model_dump())

#         return p_resp

#     def update_obj(
#         self,
#         session: Session,
#         obj_id: UUID,
#         p_model: VerifierUpdate,
#     ) -> None:
#         stmt = (
#             update(self.repo_schema)
#             .where(self.repo_schema.id == obj_id)
#             .values(**p_model.model_dump(exclude_unset=True))
#             .execution_options(synchronize_session="fetch")
#         )
#         session.execute(stmt)

#     def delete_obj(self, session: Session, obj_id: UUID) -> None:
#         stmt = delete(self.repo_schema).where(self.repo_schema.id == obj_id)
#         session.execute(stmt)

#     def get_obj_by_filter(
#         self, session: Session, cols: list[Column], col_vals: list[Any]
#     ):
#         stmt = select(self.repo_schema)
#         for i, col in enumerate(cols):
#             stmt = stmt.filter(col == col_vals[i])
#         db_models = session.execute(stmt).scalars().all()
#         return [self._model.model_validate(db_model) for db_model in db_models]

#     def get_col_by_filter(
#         self,
#         session: Session,
#         cols: list[str],
#         col_names: list[str],
#         col_vals: list[Any],
#     ):
#         # Create a list of column objects based on the column names provided
#         columns_to_select = [getattr(self.repo_schema, col) for col in cols]

#         # Start the query by selecting only the specified columns
#         stmt = select(*columns_to_select)

#         # Apply filters to the statement
#         for i, col_name in enumerate(col_names):
#             stmt = stmt.where(col_name == col_vals[i])

#         # Execute the query and fetch results
#         db_models = session.execute(stmt).scalars().all()

#         # Return the results
#         return db_models
