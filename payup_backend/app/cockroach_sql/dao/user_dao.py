import logging
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete, update, Connection, Column

from ...modules.user.model import UserCreate, UserUpdate, User as UserModel
from ..schemas import pwd_context, User as UserSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


class UserRepo:

    def __init__(self):
        self._schema = UserSchema

    def get_objs(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> list[UserModel]:
        stmt = select(self._schema).offset(skip).limit(limit)
        db_models = session.execute(stmt).scalars().all()
        return [UserModel.model_validate(db_model) for db_model in db_models]

    def get_obj(self, session: Session, obj_id: UUID):
        stmt = select(self._schema).filter(self._schema.id == obj_id)
        db_model = session.execute(stmt).scalars().first()
        return UserModel.model_validate(db_model)

    def create_obj(self, session: Session, p_model: UserCreate) -> UserModel:
        # stmt = insert(UserSchema).values(**p_model.model_dump(), owner_id=user_id)
        db_model = self._schema(**p_model.model_dump(exclude=["m_pin"]))
        if p_model.m_pin is not None:
            db_model.set_password(p_model.m_pin.get_secret_value())
        db_model.is_active = True
        logger.info("db_model : %s", db_model)
        session.add(db_model)
        session.commit()
        session.refresh(db_model)

        p_resp = UserModel.model_validate(db_model)
        logger.info("[response]-[%s]", p_resp.model_dump())

        return p_resp

    def create_user_item_2(self, conn: Connection, p_model: UserCreate) -> UserModel:
        db_model = self._schema(**p_model.model_dump(exclude=["m_pin"]))
        if p_model.m_pin is not None:
            db_model.set_password(p_model.m_pin.get_secret_value())
        db_model.is_active = True

        model_data = {
            c.name: getattr(db_model, c.name)
            for c in self._schema.__table__.columns
            if c.name != "id"
        }
        logger.info("[model data]-[%s]", model_data)

        # Prepare the insert statement
        stmt = insert(self._schema).values(**model_data)
        # Prepare the insert statement

        # Execute the statement directly using the connection
        res = conn.execute(stmt)

        # Convert the result to a Pydantic model
        logger.info("[res]-[]")
        user_data = None
        while res:
            user_data = dict(res)
            logger.info("[res]-[%s]", user_data)
        if user_data:
            return UserModel(**user_data)

        raise ValueError("Failed to create user")

    def update_obj(self, session: Session, obj_id: UUID, p_model: UserUpdate) -> None:
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
        return [UserModel.model_validate(db_model) for db_model in db_models]

    def get_user_txn(
        self, session: Session, phone_number: str = None, user_id: UUID = None
    ):
        """
        Select a row of the users table, and return the row as a User object.

        Arguments:
            session {.Session} -- The active session for the database connection.

        Keyword Arguments:
            phone_number {String} -- The user's phone_number. (default: {None})
            user_id {UUID} -- The user's unique ID. (default: {None})

        Returns:
            User -- A User object.
        """
        if phone_number:
            stmt = select(self._schema).filter(
                self._schema.phone_number == phone_number
            )
        elif user_id:
            stmt = select(self._schema).filter(self._schema.id == user_id)
        else:
            return None

        db_model = session.execute(stmt).scalars().first()
        return UserModel.model_validate(db_model) if db_model else None
