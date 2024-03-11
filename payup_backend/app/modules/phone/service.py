"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status

from ...cockroach_sql.database import database
from ...config.constants import get_settings
from .model import PhoneResponse, PhoneUpdate
from ...config.errors import NotFoundError

from ...cockroach_sql.dao.phone_dao import PhoneRepo
from ..phone.model import PhoneUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

constants = get_settings()


class PhoneService:
    """
    The class methods interact with multiple services to facilitate auth endpoints.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.engine = database.engine
        self.sessionmaker = sessionmaker(bind=self.engine)

        self.phone_repo = PhoneRepo()

    async def get_phone_details(self, user_id: UUID) -> list[PhoneResponse]:
        """send otp via sms"""
        try:
            with self.sessionmaker() as session:
                # query for phone number if already exist get if, else create phone entity in db
                p_models = self.phone_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[
                        (self.phone_repo._schema.user_id, user_id),
                    ],
                )
                logger.debug("phones : %s", p_models)
                session.commit()

            return [PhoneResponse.model_validate(p_model) for p_model in p_models]
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args,
            ) from err

    async def set_phone_pin(
        self, phone_id: UUID, pin: int, user_id: UUID
    ) -> PhoneResponse:
        """
        Wraps a `run_transaction` call that updates a phone.

        Arguments:
            phone_id {UUID} -- The user's varified phone_numbers' database id.
            pin {int} -- A 6-digit pin created by user.
            user_id {UUID} -- id of the user owning the phone_number

        """
        try:
            with self.sessionmaker() as session:
                p_model = await self.phone_repo.update_obj(
                    session=session,
                    obj_id=phone_id,
                    p_model=PhoneUpdate(m_pin=pin),
                    col_filters=[
                        (self.phone_repo._schema.user_id, user_id),
                        (self.phone_repo._schema.is_primary, True),
                        (self.phone_repo._schema.verified, True),
                    ],
                )

                if len(p_model) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="phone number not verified as a primary account number",
                    )
                session.commit()
            return PhoneResponse.model_validate(p_model)
        except NotFoundError as err:
            raise NotFoundError from err
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args,
            ) from err
