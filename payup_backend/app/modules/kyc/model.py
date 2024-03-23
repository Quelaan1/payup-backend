import re
import logging
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict, model_validator, Field

# model_config = ConfigDict(from_attributes=True)
from ...cockroach_sql.db_enums import KycType
from ...models.py_models import BaseResponse

logger = logging.getLogger(__name__)


class KycBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        # use_enum_values=True,
    )

    entity_id: str
    entity_type: KycType

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
