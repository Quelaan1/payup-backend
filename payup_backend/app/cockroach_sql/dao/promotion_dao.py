import logging
from ..schemas import PromotionSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...modules.promotion.model import Promotion as PromotionModel

logger = logging.getLogger(__name__)


class PromotionRepo:
    def __init__(self):
        self._repo_schema = PromotionSchema

    async def get_promotion(self, session: AsyncSession) -> list[PromotionModel]:
        """get promotions list"""
        stmt = select(self._repo_schema)
        result = await session.execute(stmt)
        db_models = result.scalars().all()

        response = [
            PromotionModel(
                id=db_model.id,
                discount=db_model.discount,
                title=db_model.title,
                description=db_model.description,
                image_url=db_model.image_url,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            )
            for db_model in db_models
        ]

        return response
