import base64
import binascii
import re
import logging
from typing import Optional
from pydantic import (
    BaseModel,
    UUID4,
    ConfigDict,
    model_validator,
    # Field,
)
from fastapi import HTTPException, status

from payup_backend.app.utils.encryption_utils import (
    decrypt_entity_id,
    encrypt_entity_id,
)

# model_config = ConfigDict(from_attributes=True)
from ...cockroach_sql.db_enums import KycType
from ...models.py_models import BaseResponse
from ...config.constants import get_settings
from ...helperClass.verifications.kyc_pan.sandbox.models import SplitAddressModel
from ..profile.model import ProfileWithUserId

logger = logging.getLogger(__name__)

constants = get_settings()


class UserKycRelationBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        extra="ignore",
        # use_enum_values=True,
    )

    kyc_id: UUID4
    user_id: UUID4


class KycLookupBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        extra="ignore",
        # use_enum_values=True,
    )

    entity_id: str
    entity_type: KycType


class KycLookupCreate(KycLookupBase):
    """minimum item information"""


class KycLookup(KycLookupCreate):
    """minimum item information"""


class KycBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        extra="ignore",
        # use_enum_values=True,
    )

    entity_id: Optional[str] = None
    entity_type: KycType

    @model_validator(mode="before")
    def validate_entity_id(self):
        value1 = getattr(self, "entity_id", None)
        value2 = getattr(self, "entity_type", None)

        logger.info("value1: %s, value2: %s", value1, value2)

        if value2 == KycType.AADHAAR and value1 is not None:
            pattern = r"^\d{12}$"
            if not bool(re.match(pattern, value1)):
                raise ValueError("Invalid Aadhaar number. It must be 12 digits.")

        if value2 == KycType.PAN and value1 is not None:
            pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
            if not bool(re.match(pattern, value1.upper())):
                raise ValueError("Invalid Pan number. It must be ABCDE1234F 10 char.")

        return self


class KycPanVerifyRequest(KycBase):
    name: str
    consent: bool
    dob: str
    entity_id: str
    entity_type: int


class KycPanVerifyResponse(ProfileWithUserId):

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        extra="ignore",
    )
    name_as_per_pan_match: Optional[bool] = None
    date_of_birth_match: Optional[bool] = None
    message: Optional[str] = None


class KycUpdate(KycBase):
    verified: Optional[bool] = None
    entity_name: Optional[str] = None


class KycCreate(KycUpdate):
    birthorincorporateddate: Optional[str] = None
    entity_id_encrypted: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    zip: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    address: Optional[SplitAddressModel] = None

    @model_validator(mode="after")
    def set_encrypted_id(self):
        logger.info(self)
        try:
            if self.entity_id is not None and self.entity_id_encrypted is None:
                if self.entity_type == KycType.PAN:
                    key = constants.PAYUP.PAN_KEY
                elif self.entity_type == KycType.AADHAAR:
                    key = constants.PAYUP.UIDAI_KEY
                encoded = encrypt_entity_id(self.entity_id, key)
                self.entity_id_encrypted = encoded
            return self
        except Exception as e:
            logger.error("%s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e


class Kyc(KycUpdate):
    id: UUID4
    entity_id_encrypted: Optional[str] = None

    @model_validator(mode="after")
    def set_decrypted_id(self):
        logger.info(self)

        if self.entity_id_encrypted is not None and self.entity_id is None:
            if self.entity_type == KycType.PAN:
                key = constants.PAYUP.PAN_KEY
            elif self.entity_type == KycType.AADHAAR:
                key = constants.PAYUP.UIDAI_KEY

            decoded = decrypt_entity_id(self.entity_id_encrypted, key)

            self.entity_id = decoded
        return self


class KycResponse(BaseResponse, KycBase):
    entity_name: Optional[str] = None
    internal_id: Optional[UUID4] = None
    name_as_per_pan_match: Optional[bool] = None
    date_of_birth_match: Optional[bool] = None


class KycCreateRequest(BaseModel):
    """request body to connect kycs"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        extra="ignore",
        # use_enum_values=True,
    )

    entity_id: str
    entity_type: KycType
    entity_name: str
    internal_id: UUID4


class KycAadhaarRequest(KycBase):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
    )
    ref_id: str
    otp: str


class KycAadhaarResponse(BaseResponse):
    ref_id: Optional[str] = None


class KycUpiVerifyRequest(BaseModel):
    upi_id: str


class KycUpiVerifyResponse(BaseResponse):
    verified: Optional[bool] = None
    message: Optional[str] = None
