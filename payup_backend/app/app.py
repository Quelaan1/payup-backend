"""configure app"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

from ..main import app
from .config.errors import (
    ConfigError,
    DatabaseError,
    ExternalServiceError,
    UnicornException,
    NotFoundError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    logger.info("UnicornError : %s", exc.args)
    return JSONResponse(
        status_code=status.HTTP_418_IM_A_TEAPOT,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


@app.exception_handler(ConfigError)
async def config_exception_handler(request: Request, exc: ConfigError):
    logger.info("ConfigError : %s", exc.args)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"Oops! config not set properly. There goes a rainbow..."},
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    logger.info("DatabaseError : %s", exc.args)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": f"Oops! issue with database connection. There goes a rainbow..."
        },
    )


@app.exception_handler(ExternalServiceError)
async def external_service_exception_handler(
    request: Request, exc: ExternalServiceError
):
    logger.info("ExternalServiceError : %s", exc.args)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"Service {exc.name} is down. There goes a rainbow..."},
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    logger.info("NotFoundError : %s", exc.args)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": f"Resource {exc.name} not found. There goes a rainbow..."},
    )
