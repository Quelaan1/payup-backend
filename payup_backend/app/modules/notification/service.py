import logging
from uuid import UUID
from fastapi import HTTPException, status
from payup_backend.app.cockroach_sql.database import database
from payup_backend.app.cockroach_sql.dao.device_dao import DeviceRepo
from payup_backend.app.cockroach_sql.dao.device_token_dao import DeviceTokenRepo
from payup_backend.app.modules.notification.model import (
    NotificationModel,
    NotificationPreferenceResponse,
)
from ...cockroach_sql.dao.notification_dao import (
    NotificationPreferenceRepository,
    NotificationRepository,
)
from ...dependency.expo_notification import ExpoNotification

logger = logging.getLogger(__name__)


class NotificationService:
    """
    The class methods interact with multiple services to facilitate notification endpoints.
    """

    def __init__(
        self,
    ):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.sessionmaker = database.get_session()

        self.preference_repo = NotificationPreferenceRepository()
        self.device_repo = DeviceRepo()
        self.token_repo = DeviceTokenRepo()
        self.notification_repo = NotificationRepository()
        self.expo_notification = ExpoNotification()

    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
    ):
        """
        Wraps a `session` call that sends a push notification.
        """

        try:
            async with self.sessionmaker() as session:
                async with session.begin():
                    preferences = await self.preference_repo.get_preference_by_user(
                        session=session, user_id=UUID(user_id)
                    )

                    app_notifications = getattr(preferences, "app_notifications", None)
                    if app_notifications and getattr(
                        app_notifications, notification_type
                    ):
                        devices = await self.device_repo.get_devices(
                            session=session, user_id=UUID(user_id)
                        )

                        # Send push notification
                        for device in devices:
                            tokens = await self.token_repo.get_device_tokens(
                                session=session, device_id=device.device_id
                            )
                            for token in tokens:
                                if token.token_purpose == "push_notification":
                                    # Send push notification
                                    try:
                                        await self.expo_notification.send_push_message(
                                            token=token.token,
                                            message=message,
                                            extra={"title": title},
                                            session=session,
                                        )
                                    except Exception as e:
                                        logger.error(
                                            "Push notification failed for device %s",
                                            device.device_id,
                                        )
                                        logger.error(e)

                                    logger.info(
                                        "Push notification sent to device %s",
                                        device.device_id,
                                    )

                        # Save notification record
                        notification = NotificationModel(
                            user_id=user_id,  # type: ignore
                            title=title,
                            message=message,
                            type=notification_type,
                            method="app_notification",
                        )

                        await self.notification_repo.add_notification(
                            session=session, notification=notification
                        )
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            detail_message = (
                err.args[0] if err.args else "An unexpected error occurred."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail_message
            ) from err

    async def get_preference(self, user_id: str) -> NotificationPreferenceResponse:
        """
        Wraps a `session` call that gets a list of preferences for a user.
        """
        try:
            async with self.sessionmaker() as session:
                preferences = await self.preference_repo.get_preference_by_user(
                    session=session, user_id=UUID(user_id)
                )

                await session.commit()
            return preferences
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err

    async def update_preference(
        self, user_id: str, preference
    ) -> NotificationPreferenceResponse:
        """
        Wraps a `session` call that updates a user's preference.
        """
        try:
            async with self.sessionmaker() as session:
                preferences = await self.preference_repo.update_preference(
                    session=session, user_id=UUID(user_id), preference=preference
                )

                await session.commit()
            return preferences
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.args[0]
            ) from err
