from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..schemas import NotificationPreference, Device, DeviceToken, Notification


class NotificationPreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences_by_user(self, user_id: str):
        result = await self.session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        return result.scalars().all()

    async def update_preference(self, preference: NotificationPreference):
        self.session.add(preference)
        await self.session.commit()


class DeviceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_devices_by_user(self, user_id: str):
        result = await self.session.execute(
            select(Device).where(Device.user_id == user_id)
        )
        return result.scalars().all()

    async def add_device(self, device: Device):
        self.session.add(device)
        await self.session.commit()


class DeviceTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tokens_by_device(self, device_id: str):
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.device_id == device_id)
        )
        return result.scalars().all()

    async def add_token(self, token: DeviceToken):
        self.session.add(token)
        await self.session.commit()


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_notification(self, notification: Notification):
        self.session.add(notification)
        await self.session.commit()

    async def get_notifications_by_user(self, user_id: str):
        result = await self.session.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        return result.scalars().all()
