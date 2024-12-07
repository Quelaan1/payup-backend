from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from payup_backend.app.modules.notification.model import (
    NotificationModel,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    Preferences,
)
from ..schemas import NotificationPreferenceSchema, NotificationSchema


class NotificationPreferenceRepository:
    """CRUD operations on notification preferences model"""

    def __init__(self):
        self.repo_schema = NotificationPreferenceSchema

    async def create_default_preference(self, session: AsyncSession, user_id: UUID):
        default_preferences = Preferences().dict()

        new_preference = self.repo_schema(
            user_id=user_id, preferences=default_preferences
        )
        session.add(new_preference)
        await session.commit()

    async def get_preference_by_user(
        self, session: AsyncSession, user_id: UUID
    ) -> NotificationPreferenceResponse:
        """Get notification preferences list for a user"""
        stmt = select(self.repo_schema).filter(self.repo_schema.user_id == user_id)
        result = await session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            raise HTTPException(
                status_code=404, detail="Notification preferences not found"
            )

        return NotificationPreferenceResponse(**db_model.preferences)

    async def update_preference(
        self,
        session: AsyncSession,
        user_id: UUID,
        preference: NotificationPreferenceRequest,
    ) -> NotificationPreferenceResponse:
        """Update the app_notification preference for a user"""
        stmt = select(self.repo_schema).filter(self.repo_schema.user_id == user_id)
        result = await session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            db_model.preferences = preference.dict()
            db_model.updated_at = datetime.now(pytz.UTC).replace(tzinfo=None)  # type: ignore
            await session.commit()

            return NotificationPreferenceResponse(**db_model.preferences)
        else:
            # Handle the case where the preference does not exist
            raise ValueError("Preference not found")


class NotificationRepository:
    """CRUD operations on notifications model"""

    def __init__(self):
        self.repo_schema = NotificationSchema

    async def add_notification(
        self, session: AsyncSession, notification: NotificationModel
    ):
        """Add a new notification"""
        db_model = self.repo_schema(**notification.model_dump())
        session.add(db_model)
        await session.commit()

    async def update_notification(
        self, session: AsyncSession, notification: NotificationModel
    ):
        """Update an existing notification"""
        stmt = select(self.repo_schema).filter(
            self.repo_schema.notification_id == notification.id
        )
        result = await session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            db_model.status = notification.status
            db_model.updated_at = datetime.now(pytz.UTC).replace(tzinfo=None)

    async def get_notifications_by_user(
        self, session: AsyncSession, user_id: UUID
    ) -> list[NotificationModel]:
        """Get notifications list for a user"""
        stmt = select(self.repo_schema).filter(self.repo_schema.user_id == user_id)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [NotificationModel.model_validate(db_model) for db_model in db_models]
