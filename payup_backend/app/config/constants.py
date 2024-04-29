"""loads environment constants in code"""

import os
from functools import lru_cache
from typing import Any, Union, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PayupSettings(BaseSettings):
    """creates a singleton constants instance"""

    PAN_KEY: bytes
    UIDAI_KEY: bytes

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="payup_", extra="ignore", env_file_encoding="utf-8"
    )

    def __str__(self):
        return settings_as_string(self.model_dump(), "PAYUP")

    @model_validator(mode="before")
    @classmethod
    def encode_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "PAN_KEY" in data.keys():
                val = (data.get("PAN_KEY") + "=").encode()
                data["PAN_KEY"] = val
            if "UIDAI_KEY" in data.keys():
                val = (data.get("UIDAI_KEY") + "=").encode()
                data["UIDAI_KEY"] = val
        return data


class SandboxSettings(BaseSettings):
    """creates a singleton constants instance"""

    API_KEY: str
    SECRET_KEY: str
    ACCESS_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="sandbox_", extra="ignore"
    )

    def __str__(self):
        return settings_as_string(self.model_dump(), "SANDBOX")

    def update_access_token(self, new_token: str):
        """Update the access token in settings and environment."""
        self.ACCESS_TOKEN = new_token
        os.environ["SANDBOX_ACCESS_TOKEN"] = new_token
        get_settings.cache_clear()


class CockroachSettings(BaseSettings):
    """creates a singleton constants instance"""

    PASSWORD: str
    USER: str
    CLUSTER: str
    DB: str
    DB_URI: str
    CERT_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="cockroach_", extra="ignore"
    )

    def __str__(self):
        return settings_as_string(self.model_dump(), "COCKROACH")


class TokenSettings(BaseSettings):
    """creates a singleton constants instance"""

    SECRET_KEY: str
    ALGORITHM: str
    ISSUER: str
    AUDIENCE: Union[str, list[str]]
    ACCESS_TOKEN_DURATION: int  # in minutes
    REFRESH_TOKEN_DURATION: int  # in minutes

    model_config = SettingsConfigDict(env_file=".env", env_prefix="jt_", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def check_card_number_omitted(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "AUDIENCE" in data.keys():
                val = data.get("AUDIENCE").split(",")
                data["AUDIENCE"] = val
        return data

    def __str__(self):
        return settings_as_string(self.model_dump(), "JT")


class TwilioSettings(BaseSettings):
    """creates a singleton constants instance"""

    BASE_URL: str
    ACCOUNT_SID: str
    AUTH_TOKEN: str
    SMS_SERVICE_SID: str
    PHONE_NUMBER: str

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="twilio_", extra="ignore"
    )

    def __str__(self):
        return settings_as_string(self.model_dump(), "TWILIO")


class Settings(BaseSettings):
    """creates a singleton constants instance"""

    ENV: str = "local"
    TWILIO: TwilioSettings = TwilioSettings()
    SANDBOX: SandboxSettings = SandboxSettings()
    COCKROACH: CockroachSettings = CockroachSettings()
    JT: TokenSettings = TokenSettings()
    PAYUP: PayupSettings = PayupSettings()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __str__(self):
        return settings_as_string(self.model_dump())


@lru_cache
def get_settings():
    """returns a cached instance of Settings"""
    setting = Settings()
    return setting


def settings_as_string(data: dict, prefix_key: str = "") -> str:
    """print dict items in new lines"""

    def mask_sensitive(value: str) -> str:
        if isinstance(value, str) and len(value) > 2:
            return f"{value[0]}****{value[-1]}"
        return value

    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            nested_str = settings_as_string(value, key)
            lines.append(f"{nested_str}")
        else:
            masked_value = (
                mask_sensitive(value)
                if "pass" in key.lower() or "secret" in key.lower()
                else value
            )
            lines.append(f"{prefix_key}_{key}: {masked_value}")

    return "\n".join(lines)
