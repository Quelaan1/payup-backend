import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .app.config.logging import LogConfig
from .app.config.exception_handler import CustomExceptionHandler
from .app.config.errors import (
    ConfigError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
)
from .app.config.constants import get_settings
from .app.app import router as api_router
from .app.helperClass.logging_lib import LoggingMiddleware

log_config = LogConfig()
logging.config.dictConfig(log_config.logging_config)

logger = logging.getLogger(__name__)

app = FastAPI()
app_setting = get_settings()

# adding middlewares
app.add_middleware(LoggingMiddleware, logger=logging.getLogger("[REQUEST LOGGER]"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://*",
        "http://localhost",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
