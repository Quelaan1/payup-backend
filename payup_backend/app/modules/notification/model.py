from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class NotificationPreferenceRequest(BaseModel):
    preference_category: str
    email: bool
    sms: bool
    push: bool
    in_app: bool


class NotificationPreferenceResponse(BaseModel):
    preference_category: str
    email: bool
    sms: bool
    push: bool
    in_app: bool


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    sent_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
