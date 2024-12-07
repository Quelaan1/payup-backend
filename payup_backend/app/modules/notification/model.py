from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime


class NotificationSettings(BaseModel):
    transactions: bool = Field(default=True)


class Preferences(BaseModel):
    app_notifications: NotificationSettings = Field(
        default_factory=NotificationSettings
    )


class NotificationPreferenceRequest(Preferences):
    pass


class NotificationPreferenceResponse(Preferences):
    pass


class NotificationModel(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str
    method: str
    status: Optional[str] = Field(default="sent")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
