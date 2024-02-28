import logging

from fastapi import FastAPI

# from sqlalchemy import text

from payup_backend.app.config.constants import get_settings

# from app.cockroach_sql.database import Session
from payup_backend.app.routers.api_routes import router as api_router
from payup_backend.app.helperClass.logging_lib import LoggingMiddleware

# from app.routes.auth.otp import router as otp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)-5d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

app = FastAPI()
app_setting = get_settings()
logger.info("settings : \n%s", app_setting)

app.add_middleware(LoggingMiddleware, logger=logging.getLogger("[REQUEST LOGGER]"))


@app.get("/")
async def root():
    return {"message": "Welcome to PayUp"}


app.include_router(api_router, prefix="/api")


# app.include_router(otp_router)
