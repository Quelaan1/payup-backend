"""class that encapsulated api router"""

import logging
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from .model import ItemCreate, Item as ItemModel
from .service import ItemService
from ...dependency.authentication import get_current_active_user, signup_oauth2_schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s | %(lineno)-5d : %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)


class ItemHandler:

    def __init__(self, name: str):
        self.name = name
        self.item_service = ItemService()
        self.router = APIRouter()

        self.router.add_api_route(
            "/healthz", self.hello, methods=["GET"], tags=["health-check"]
        )
        self.router.add_api_route(
            "/",
            endpoint=self.read_items_endpoint,
            response_model=List[ItemModel],
            status_code=status.HTTP_200_OK,
            methods=["GET"],
            response_model_exclude_none=True,
        )
        self.router.add_api_route(
            "/",
            endpoint=self.create_item_endpoint,
            status_code=status.HTTP_200_OK,
            response_model=ItemModel,
            methods=["POST"],
            response_model_exclude_none=True,
        )

    def hello(self):
        logger.debug("Hello : %s", self.name)
        return {"Hello": self.name}

    async def read_items_endpoint(
        self,
        auth_user: Annotated[UUID, Depends(get_current_active_user)],
        skip: int = 0,
        limit: int = 100,
    ):
        try:
            logger.info(auth_user)
            items = self.item_service.get_items(skip=skip, limit=limit)
            return items
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    async def create_item_endpoint(
        self,
        item: ItemCreate,
        user=Depends(get_current_active_user),
    ):
        try:
            return self.item_service.create_item(item, user.id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # Additional routes like update, delete can be added similarly
