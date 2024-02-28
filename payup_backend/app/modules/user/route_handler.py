"""class that encapsulated api router"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from .model import UserCreate, User as UserModel
from .service import UserService
from ...dependency.session import authenticate_user
from ...cockroach_sql.schemas import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()


@router.get("/", response_model=List[UserModel])
def read_users(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(authenticate_user),
):
    try:
        users = user_service.get_users(skip=skip, limit=limit)
        return users
    except Exception as e:
        logger.error("got error: %s", e.args)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/", response_model=UserModel)
def create_user(
    user: UserCreate,
):
    try:
        return user_service.create_user(user)
    except Exception as e:
        logger.error("got error: %s", e.args)
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Additional routes like update, delete can be added similarly
