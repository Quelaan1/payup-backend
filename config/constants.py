"""loads environment constants in code"""

import os


class ConstantsNamespace:
    """stores code constants"""

    __slots__ = ()
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    TWILIO_BASE_URL = os.getenv("TWILIO_BASE_URL")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_SMS_SERVICE_SID = os.getenv("TWILIO_SMS_SERVICE_SID")
    SANDBOX_API_KEY = os.getenv("SANDBOX_API_KEY")
    SANDBOX_SECRET_KEY = os.getenv("SANDBOX_SECRET_KEY")

    def __str__(self):
        class_attrs = {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith("__") and not callable(getattr(self, attr))
        }
        return str(class_attrs)
