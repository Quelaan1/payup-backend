"""custom settings for logging"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    ENV: str = "local"
    LOG_FORMAT: str = (
        "%(levelprefix)s | %(asctime)s | %(name)s | %(module)s | %(lineno)d | %(message)s"
    )
    LOG_LEVEL: str = "DEBUG"
    version: int = 1
    disable_existing_loggers: bool = False

    @model_validator(mode="after")
    def set_log_level_based_on_env(self):
        env = self.ENV
        if env == "production":
            self.LOG_LEVEL = "INFO"
        else:
            self.LOG_LEVEL = "DEBUG"

        return self

    @property
    def logging_config(self):
        return {
            "version": self.version,
            "disable_existing_loggers": self.disable_existing_loggers,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": self.LOG_FORMAT,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["default"],
                    "level": self.LOG_LEVEL,
                },
                "twilio.http_client": {  # Specific logger configuration for twilio
                    "handlers": ["default"],
                    "level": "WARNING",
                },
            },
        }
