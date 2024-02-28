"""class that encapsulated api router"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from .model import ItemCreate, Item as ItemModel
from .service import ItemService
from ...dependency.session import authenticate_user
from ...cockroach_sql.schemas import User


router = APIRouter()
item_service = ItemService()


@router.get("/", response_model=List[ItemModel])
def read_items(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(authenticate_user),
):
    try:
        items = item_service.get_items(skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/", response_model=ItemModel)
def create_item(
    item: ItemCreate,
    user: User = Depends(authenticate_user),
):
    try:
        return item_service.create_item(item, user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Additional routes like update, delete can be added similarly
