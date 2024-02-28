from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict

# model_config = ConfigDict(from_attributes=True)


class KycBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )

    entity_id: str
    entity_type: int


class KycCreate(KycBase):
    owner_id: UUID4
    entity_name: Optional[str] = None
    verified: Optional[bool] = None


class KycUpdate(KycBase):
    verified: Optional[bool] = None
    entity_name: Optional[str] = None


class Kyc(KycUpdate):
    owner_id: UUID4
