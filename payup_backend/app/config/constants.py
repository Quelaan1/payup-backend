"""loads environment constants in code"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    def __str__(self):
        return settings_as_string(self.model_dump(), "COCKROACH")


class TwilioSettings(BaseSettings):
    """creates a singleton constants instance"""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="twilio_", extra="ignore"
    )
    BASE_URL: str
    ACCOUNT_SID: str
    AUTH_TOKEN: str
    SMS_SERVICE_SID: str

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


@lru_cache
def get_settings():
    """returns a cached instance of Settings"""
    return Settings()


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
