import re
import logging
import base64
from typing import Optional, Any
from pydantic_core.core_schema import FieldValidationInfo
from pydantic import (
    BaseModel,
    UUID4,
    ConfigDict,
    validator,
    field_validator,
    model_validator,
    Field,
    computed_field,
)
from cryptography.fernet import Fernet

# model_config = ConfigDict(from_attributes=True)
from ...cockroach_sql.db_enums import KycType
from ...models.py_models import BaseResponse
from ...config.constants import get_settings

logger = logging.getLogger(__name__)

constants = get_settings()


class KycBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        # use_enum_values=True,
    )

    entity_id: Optional[str] = None
    entity_type: KycType
    entity_id_encrypted: Optional[bytes] = None

    @model_validator(mode="after")
    def validate_entity_id(self):
        value1 = self.entity_id
        value2 = self.entity_type
        if value2 == KycType.AADHAAR:
            pattern = r"^\d{12}$"
            if not bool(re.match(pattern, value1)):
                raise ValueError("Invalid Aadhaar number. It must be 12 digits.")

        if value2 == KycType.PAN:
            pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
            if not bool(re.match(pattern, value1.upper())):
                raise ValueError("Invalid Pan number. It must be ABCDE1234F 10 char.")
        return self

    @validator("entity_id", always=True, pre=True)
    @classmethod
    def set_encrypted_id(cls, v: Optional[str], values: dict[str, Any]):
        if v is not None:
            if values["entity_type"] == KycType.PAN.value:
                key = constants.PAYUP.PAN_KEY
            elif values["entity_type"] == KycType.AADHAAR.value:
                key = constants.PAYUP.UIDAI_KEY

            coder = Fernet(key)
            encoded = coder.encrypt(v.encode())
            values["entity_id_encrypted"] = encoded
        return v

    @validator("entity_id_encrypted", always=True, pre=True)
    @classmethod
    def set_decrypted_id(cls, v: Optional[str], values: dict[str, Any]):
        if v is not None and "entity_id" not in values.keys():
            # Simple base64 decoding, replace with actual decryption in production
            if values["entity_type"] == KycType.PAN.value:
                key = constants.PAYUP.PAN_KEY
            elif values["entity_type"] == KycType.AADHAAR.value:
                key = constants.PAYUP.UIDAI_KEY

            coder = Fernet(key)
            decoded = coder.decrypt(v.encode())
            values["entity_id"] = decoded
        return v


class KycCreate(KycBase):
    owner_id: UUID4
    entity_name: Optional[str] = None
    verified: Optional[bool] = None


class KycUpdate(KycBase):
    verified: Optional[bool] = None
    entity_name: Optional[str] = None


class Kyc(KycUpdate):
    owner_id: UUID4


class KycResponse(BaseResponse, KycBase):
    entity_name: Optional[str] = None


class AadhaarKycRequest(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
    )
    ref_id: str
    otp: str
    aadhaar_number: str = Field(..., pattern="^\d{12}$")


class AadhaarKycResponse(BaseResponse):
    ref_id: Optional[str] = None
