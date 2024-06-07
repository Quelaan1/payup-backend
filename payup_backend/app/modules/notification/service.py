from ...cockroach_sql.dao.notification_dao import (
    NotificationPreferenceRepository,
    DeviceRepository,
    DeviceTokenRepository,
    NotificationRepository,
)
from ...cockroach_sql.schemas import Notification


class NotificationService:
    def __init__(
        self,
    ):
        self.preference_repo = NotificationPreferenceRepository
        self.device_repo = DeviceRepository
        self.token_repo = DeviceTokenRepository
        self.notification_repo = NotificationRepository

    async def send_notification(self, user_id: str, title: str, message: str):
        devices = await self.device_repo.get_devices_by_user(user_id)
        preferences = await self.preference_repo.get_preferences_by_user(user_id)
        # Logic to check preferences and send notifications

        # Example: Send push notification
        for device in devices:
            tokens = await self.token_repo.get_tokens_by_device(device.device_id)
            for token in tokens:
                if token.token_purpose == "push":
                    # Send push notification
                    pass

        # Save notification record
        notification = Notification(user_id=user_id, title=title, message=message)
        await self.notification_repo.add_notification(notification)
