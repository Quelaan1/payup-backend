from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone


class DeviceBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class Device(DeviceBase):
    user_id: UUID
    device_id: UUID
    device_type: str
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceRegistrationRequest(BaseModel):
    device_id: UUID
    device_type: str


class DeviceRegistrationResponse(BaseModel):
    message: Optional[str] = None


class DeviceListResponse(BaseModel):
    Devices: list[Device]
    message: Optional[str] = None


class DeviceDeleteRequest(BaseModel):
    user_id: UUID
    device_id: UUID


class DeviceDeleteResponse(BaseModel):
    message: Optional[str] = None
