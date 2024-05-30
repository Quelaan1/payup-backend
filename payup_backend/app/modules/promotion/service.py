import logging
from fastapi import HTTPException, status
from ...cockroach_sql.dao.promotion_dao import PromotionRepo
from ...cockroach_sql.database import database
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PromotionService:
    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.engine = database.engine
        self.sessionmaker = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self._repo = PromotionRepo()

    async def get_promotion(self):
        try:
            async with self.sessionmaker() as session:
                promotions = await self._repo.get_promotion(session=session)
                await session.commit()

            if not promotions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Promotions not found",
                )

            return promotions
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            )
