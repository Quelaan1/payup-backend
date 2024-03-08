"""configure app"""

import logging
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .errors import (
    ConfigError,
    DatabaseError,
    ExternalServiceError,
    UnicornException,
    NotFoundError,
)
from ..models.py_models import BaseResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s | %(lineno)d : %(message)s",
)
logger = logging.getLogger(__name__)


class CustomExceptionHandler:

    @classmethod
    def http_exception_handler(cls, request: Request, exc: HTTPException):
        errs = exc.args
        logger.info("UnicornError : %s", errs)

        msg = ""
        for db in errs:
            msg = msg + str(db) + ", "
        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=detail
        )

    @classmethod
    def validation_exception_handler(
        cls, request: Request, exc: RequestValidationError
    ):
        errs = exc.errors()
        logger.info("UnicornError : %s", errs)

        msg = ""
        for db in errs:
            msg = msg + db["loc"][1] + ":" + db["msg"] + ", "
        detail = BaseResponse(message=msg).model_dump()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=detail
        )

    @classmethod
    def unicorn_exception_handler(cls, request: Request, exc: UnicornException):
        logger.info("UnicornError : %s", exc.args)
        detail = BaseResponse(
            message=f"Oops! {exc.name} did something. There goes a rainbow..."
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_418_IM_A_TEAPOT, content=detail)

    @classmethod
    def config_exception_handler(cls, request: Request, exc: ConfigError):
        logger.info("ConfigError : %s", exc.args)
        detail = BaseResponse(
            message="Oops! config not set properly. There goes a rainbow..."
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=detail,
        )

    @classmethod
    def database_exception_handler(cls, request: Request, exc: DatabaseError):
        logger.info("DatabaseError : %s", exc.args)
        detail = BaseResponse(
            message="Oops! issue with database connection. There goes a rainbow..."
        ).model_dump()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def external_service_exception_handler(
        cls, request: Request, exc: ExternalServiceError
    ):
        detail = BaseResponse(
            message=f"Service {exc.name} is down. There goes a rainbow..."
        ).model_dump()
        logger.info("ExternalServiceError : %s", exc.args)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=detail
        )

    @classmethod
    def not_found_exception_handler(cls, request: Request, exc: NotFoundError):
        detail = BaseResponse(
            message=f"Resource {exc.name} not found. There goes a rainbow..."
        ).model_dump()
        logger.info("NotFoundError : %s", exc.args)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=detail)
