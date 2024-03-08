import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from .app.config.exception_handler import CustomExceptionHandler
from .app.config.errors import (
    ConfigError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
)
from .app.config.constants import get_settings
from .app.routers.api_routes import router as api_router
from .app.helperClass.logging_lib import LoggingMiddleware

# from app.routes.auth.otp import router as otp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s | %(lineno)-5d : %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

app = FastAPI()
app_setting = get_settings()

# adding middlewares
app.add_middleware(LoggingMiddleware, logger=logging.getLogger("[REQUEST LOGGER]"))

# adding exception handlers
app.add_exception_handler(HTTPException, CustomExceptionHandler.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, CustomExceptionHandler.validation_exception_handler
)
app.add_exception_handler(ConfigError, CustomExceptionHandler.config_exception_handler)
app.add_exception_handler(
    NotFoundError, CustomExceptionHandler.not_found_exception_handler
)
app.add_exception_handler(
    DatabaseError, CustomExceptionHandler.database_exception_handler
)
app.add_exception_handler(
    ExternalServiceError, CustomExceptionHandler.external_service_exception_handler
)


@app.get("/")
async def root():
    return {"message": "Welcome to PayUp"}


app.include_router(api_router, prefix="/api")
