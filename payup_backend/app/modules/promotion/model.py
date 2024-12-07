from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Promotion(BaseModel):
    id: int
    discount: str
    title: str
    description: str
    image_url: str
    created_at: datetime
    updated_at: datetime


class PromotionResponse(BaseModel):
    promotions: list[Promotion]
