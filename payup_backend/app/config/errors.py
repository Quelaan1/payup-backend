"""Add your custom errors."""


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


class ConfigError(Exception):
    """Custom exception for configuration errors."""


class DatabaseError(Exception):
    """Custom exception for database errors."""


class ExternalServiceError(Exception):
    """Custom exception for external services errors."""

    def __init__(self, name: str):
        self.name = name


class NotFoundError(Exception):
    """Custom exception for resource not found in database."""

    def __init__(self, name: str):
        self.name = name
