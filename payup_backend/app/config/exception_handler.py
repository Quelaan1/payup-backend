"""configure app"""

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


class CustomExceptionHandler:

    @classmethod
    def http_exception_handler(cls, request: Request, exc: HTTPException):
        msg = exc.detail
        logger.info("Http exception Error : %s", exc)

        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(status_code=exc.status_code, content=detail)

    @classmethod
    def validation_exception_handler(
        cls, request: Request, exc: RequestValidationError
    ):
        errs = exc.errors()
        logger.info("UnicornError : %s", errs)

        msg = ""
        for db in errs:
            msg = msg + db["loc"][0] + ":" + db["msg"] + ", "
        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=detail
        )

    @classmethod
    def token_exception_handler(cls, request: Request, exc: TokenException):
        logger.info("Token Error : %s", exc.detail)
        detail = BaseResponse(message=f"{exc.name} : {exc.detail}").model_dump()
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=detail)

    @classmethod
    def config_exception_handler(cls, request: Request, exc: ConfigError):
        logger.info("ConfigError : %s", exc.args)
        detail = BaseResponse(message="Oops! config not set properly.").model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=detail,
        )

    @classmethod
    def database_exception_handler(cls, request: Request, exc: DatabaseError):
        logger.info("DatabaseError : %s", exc.args)
        detail = BaseResponse(
            message="Oops! issue with database connection."
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def external_service_exception_handler(
        cls, request: Request, exc: ExternalServiceError
    ):
        detail = BaseResponse(message=f"Service {exc.name} is down.").model_dump()
        logger.info("ExternalServiceError : %s", exc.args)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def not_found_exception_handler(cls, request: Request, exc: NotFoundError):
        detail = BaseResponse(message=f"Resource {exc.name} not found.").model_dump()
        logger.info("NotFoundError : %s", exc.detail)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=detail)
