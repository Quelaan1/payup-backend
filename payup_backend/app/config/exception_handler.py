"""configure app"""

import enum
import json
import logging
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .errors import (
    ConfigError,
    DatabaseError,
    ExternalServiceError,
    TokenException,
    NotFoundError,
)
from ..models.py_models import BaseResponse

logger = logging.getLogger(__name__)


def serialize_enum(obj):
    if isinstance(obj, enum.Enum):
        return obj.name


class CustomExceptionHandler:

    @classmethod
    def http_exception_handler(cls, request: Request, exc: HTTPException):
        logger.error("%s", exc.detail)
        if isinstance(exc.detail, str):
            msg = exc.detail
        elif isinstance(exc.detail, tuple):
            msg = ""
            for i, data in enumerate(exc.detail):
                msg = msg + ": " * (i > 0) + str(data)
        else:
            msg = str(exc.detail)

        if exc.status_code == 500:
            msg = "Something went wrong, please try again later."

        logger.error("Http exception Error : %s", exc)

        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(status_code=exc.status_code, content=detail)

    @classmethod
    def validation_exception_handler(
        cls, request: Request, exc: RequestValidationError
    ):
        errs = exc.errors()
        logger.error("UnicornError : %s", errs)

        msg = ""
        for db in errs:
            msg = msg + db["loc"][0] + ":" + db["msg"] + ", "
        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=detail
        )

    @classmethod
    def token_exception_handler(cls, request: Request, exc: TokenException):
        logger.error("Token Error : %s", exc.detail)
        detail = BaseResponse(message=f"{exc.name} : {exc.detail}").model_dump()
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=detail)

    @classmethod
    def config_exception_handler(cls, request: Request, exc: ConfigError):
        logger.error("ConfigError : %s", exc.args)
        detail = BaseResponse(message="Oops! config not set properly.").model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=detail,
        )

    @classmethod
    def database_exception_handler(cls, request: Request, exc: DatabaseError):
        logger.error("DatabaseError : %s", exc.args)
        detail = BaseResponse(
            message="Something went wrong, please try again later."
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def external_service_exception_handler(
        cls, request: Request, exc: ExternalServiceError
    ):
        logger.error("Service %s is down.", exc.name)
        detail = BaseResponse(
            message="Something went wrong, please try again later"
        ).model_dump()
        logger.error("ExternalServiceError : %s", exc.args)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def not_found_exception_handler(cls, request: Request, exc: NotFoundError):
        if exc.detail is not None:
            detail = BaseResponse(message=f"{exc.detail}.").model_dump()
        else:
            detail = BaseResponse(
                message=f"Resource {exc.name} not found."
            ).model_dump()
        logger.error("NotFoundError : %s", exc.detail)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=detail)
