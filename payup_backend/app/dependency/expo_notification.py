import rollbar
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
from tenacity import retry, stop_after_attempt, wait_fixed
from payup_backend.app.cockroach_sql.dao.device_token_dao import DeviceTokenRepo


class ExpoNotification:
    def __init__(self):
        self.push_client = PushClient()
        self.token_repo = DeviceTokenRepo()

    # Retry decorator with tenacity
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def send_push_message(self, token, message, extra=None, session=None):
        try:
            response = PushClient().publish(
                PushMessage(to=token, body=message, data=extra)
            )
        except PushServerError as exc:
            # Encountered some likely formatting/validation error.
            rollbar.report_exc_info(
                extra_data={
                    "token": token,
                    "message": message,
                    "extra": extra,
                    "errors": exc.errors,
                    "response_data": exc.response_data,
                }
            )
            raise
        except (ConnectionError, HTTPError) as exc:
            # Encountered some Connection or HTTP error - retry a few times in
            # case it is transient.
            rollbar.report_exc_info(
                extra_data={"token": token, "message": message, "extra": extra}
            )
            raise exc

        try:
            # We got a response back, but we don't know whether it's an error yet.
            # This call raises errors, so we can handle them with normal exception
            # flows.
            response.validate_response()
        except DeviceNotRegisteredError:
            # Delete the token
            await self.token_repo.delete_device_token(token=token, session=session)
            raise HTTPError("Device not registered")
        except PushTicketError as exc:
            # Encountered some other per-notification error.
            rollbar.report_exc_info(
                extra_data={
                    "token": token,
                    "message": message,
                    "extra": extra,
                    "push_response": exc.push_response._asdict(),
                }
            )
            raise exc
