from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone


class DeviceTokenBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class DeviceToken(DeviceTokenBase):
    token_id: UUID
    device_id: UUID
    token: str
    token_purpose: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceTokenCreateRequest(BaseModel):
    device_id: UUID
    token: str
    token_purpose: str


class DeviceTokenCreateResponse(BaseModel):
    message: Optional[str] = None


class DeviceTokenUpdateRequest(BaseModel):
    device_id: UUID
    token: str
    token_purpose: str


class DeviceTokenUpdateResponse(BaseModel):
    message: Optional[str] = None
