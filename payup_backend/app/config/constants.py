"""loads environment constants in code"""

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from google.cloud import secretmanager


class SandboxSettings(BaseSettings):
    """creates a singleton constants instance"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="sandbox_", extra="ignore"
    )

    API_KEY: str
    SECRET_KEY: str

    def __str__(self):
        return settings_as_string(self.model_dump(), "SANDBOX")


class CockroachSettings(BaseSettings):
    """creates a singleton constants instance"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="cockroach_", extra="ignore"
    )

    PASSWORD: str
    USER: str
    CLUSTER: str
    DB: str
    DB_URI: str
    DB_CERT: Optional[str] = None

    def __init__(self):
        self.set_db_cert()

    def __str__(self):
        return settings_as_string(self.model_dump(), "COCKROACH")

        # Access the secret version.
        # Create the Secret Manager client.

    def set_db_cert(self):
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(
            request={"name": "projects/803591674308/secrets/Cockroach_DB/versions/1"}
        )

        payload = response.payload.data.decode("UTF-8")
        self.DB_CERT = payload
        print(f"Plaintext: {payload}")


class TwilioSettings(BaseSettings):
    """creates a singleton constants instance"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="twilio_", extra="ignore"
    )
    BASE_URL: str
    ACCOUNT_SID: str
    AUTH_TOKEN: str
    SMS_SERVICE_SID: str
    PHONE_NUMBER: str

    def __str__(self):
        return settings_as_string(self.model_dump(), "TWILIO")


class Settings(BaseSettings):
    """creates a singleton constants instance"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "local"
    TWILIO: TwilioSettings = TwilioSettings()
    SANDBOX: SandboxSettings = SandboxSettings()
    COCKROACH: CockroachSettings = CockroachSettings()

    def __str__(self):
        return settings_as_string(self.model_dump())


# @lru_cache
def get_settings():
    """returns a cached instance of Settings"""
    setting = Settings()
    print(setting.model_dump())
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
