"""interface to sandbox api"""

import logging
import requests
from typing import Optional
from fastapi import HTTPException, status

from .models import (
    SandboxPANVerifyData,
    SandboxPANVerifyResponse,
    SandboxAadhaarVerifyResponse,
    SandboxAadhaarOtpResponse,
    SandboxUpiVerifyResponse,
)
from .....modules.kyc.pan.pan_model import (
    AadhaarVerifyRequestSchema,
    AadhaarOtpRequestSchema,
)
from .....config.constants import get_settings


logger = logging.getLogger(__name__)

constants = get_settings()


class Sandbox:
    _base_url = "https://api.sandbox.co.in"

    def __init__(self, sandbox_api_key: str, sandbox_secret: str):
        self.api_key = sandbox_api_key
        self.api_secret = sandbox_secret
        self.access_token = constants.SANDBOX.ACCESS_TOKEN
        self.token_expiry = None

    async def authenticate(self):
        if not self.api_key or not self.api_secret:
            logger.error("API key or secret is missing.")
            raise HTTPException(
                detail="Something went wrong, please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        url = f"{self._base_url}/authenticate"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "x-api-version": "1.0",
        }

        try:
            response = requests.post(url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            constants.SANDBOX.update_access_token(self.access_token)
            logger.info(constants.SANDBOX.ACCESS_TOKEN == self.access_token)
        except requests.RequestException as e:
            logger.error("Failed to authenticate: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=response.status_code
            ) from e
        except Exception as e:
            logger.error("Failed to authenticate: %s", e)
            raise HTTPException(
                detail="Something went wrong, please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from e
        finally:
            response.close()

    async def refresh_token(self, code: Optional[int] = None):
        if not self.access_token or code is None:
            logger.error("Authentication is required before refreshing the token.")
            return await self.authenticate()
        if code == 403:
            logger.info("got 403 response")
            return await self.authenticate()

        url = f"{self._base_url}/authorize"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
        }
        logger.info("Refreshing token...")

        try:
            response = requests.post(url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            # got 403 response
            code = data.get("code")
            if code == 200:
                self.access_token = data.get("access_token")
                constants.SANDBOX.update_access_token(self.access_token)

            logger.info("Token refreshed successfully.")
        except requests.RequestException as e:
            logger.error("Failed to refresh token: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=response.status_code
            ) from e
        except Exception as e:
            logger.error("Failed to authenticate: %s", e)
            raise HTTPException(
                detail="Something went wrong, please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from e
        finally:
            response.close()

    async def verifyPan(self, pan_data: SandboxPANVerifyData):

        url = f"{self._base_url}/kyc/pan/verify"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
            "content-type": "application/json",
        }
        try:
            payload = pan_data.model_dump(by_alias=True)
            logger.info("payload: \n%s", payload)
            response = requests.post(url, headers=headers, timeout=20, json=payload)
            logger.info("status code: %s", response.status_code)
            data = response.json()

            if response.status_code == 403:
                logger.error(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(url, headers=headers, timeout=20, json=payload)

            if response.status_code == 400:
                logger.info("request error..%s", str(response.content))
                message = data.get("message", "No message found")
                logger.error("Message: %s", message)
                raise HTTPException(status_code=500, detail=message)

            response.raise_for_status()
            return SandboxPANVerifyResponse.model_validate(response.json())
        except requests.RequestException as e:
            data = response.json()
            message = data.get("message", "No message found")
            logger.error("Message: %s", message)
            raise HTTPException(detail=message, status_code=response.status_code) from e
        except Exception as e:
            logger.error("Failed to authenticate: %s", e)
            raise HTTPException(
                detail="Something went wrong, please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from e
        finally:
            response.close()

    async def old_verifyPan(self, pan_number):

        url = f"{self._base_url}/pans/{pan_number}/verify?consent=y&reason=For%20KYC%20of%20User"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
        }
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code >= 400:
                logger.info(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                data = response.json()
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.get(url, headers=headers, timeout=20)

            response.raise_for_status()
            return SandboxPANVerifyResponse.model_validate(response.json())
        except requests.RequestException as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=response.status_code
            ) from e
        except Exception as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        finally:
            response.close()

    async def otpAadhaar(self, body: AadhaarOtpRequestSchema):

        url = f"{self._base_url}/kyc/aadhaar/okyc/otp"

        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                url, json=body.model_dump(), headers=headers, timeout=20
            )
            if response.status_code >= 400:
                logger.info("Token expired. Refreshing token...")
                data = response.json()
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(
                    url, json=body.model_dump(), headers=headers, timeout=20
                )

            response.raise_for_status()
            return SandboxAadhaarOtpResponse.model_validate(response.json())
        except requests.RequestException as e:
            logger.error("Failed to send OTP: %s", e.args)
            raise HTTPException(
                detail=e.args[0], status_code=response.status_code
            ) from e
        except Exception as e:
            logger.error("Failed to send OTP: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        finally:
            response.close()

    async def verifyAadhaar(self, body: AadhaarVerifyRequestSchema):

        url = f"{self._base_url}/kyc/aadhaar/okyc/otp/verify"

        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
            "content-type": "application/json",
        }

        try:
            payload = body.model_dump()
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            logger.info("status code: %s", response.status_code)
            data = response.json()

            if response.status_code == 403:
                logger.error(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(url, headers=headers, timeout=20, json=payload)
                data = response.json()

            if response.status_code == 400:
                logger.info("request error..%s", str(response.content))
                message = data.get("message", "No message found")
                logger.error("Message: %s", message)
                raise HTTPException(status_code=500, detail=message)

            if response.status_code == 500:
                logger.info("request error..%s", str(response.content))
                message = data.get("message", "No message found")
                raise HTTPException(
                    detail=message, status_code=status.HTTP_400_BAD_REQUEST
                )

            response.raise_for_status()
            return SandboxAadhaarVerifyResponse.model_validate(response.json())
        except requests.RequestException as e:
            data = response.json()
            message = data.get("message", "No message found")
            logger.error("Message: %s", message)
            raise HTTPException(detail=message, status_code=response.status_code) from e
        except HTTPException as err:
            raise err
        except Exception as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        finally:
            response.close()

    async def verifyUpi(self, upi_id: str):
        url = f"{self._base_url}/bank/upi/{upi_id}"

        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
            "content-type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=20)
            logger.info("status code: %s", response.status_code)
            data = response.json()

            if response.status_code == 403:
                logger.error(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(
                    url,
                    headers=headers,
                    timeout=20,
                )
                data = response.json()

            if response.status_code == 503:
                logger.error(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(
                    url,
                    headers=headers,
                    timeout=20,
                )
                data = response.json()

            if response.status_code == 500:
                logger.info("request error..%s", str(response.content))
                message = data.get("message", "No message found")
                raise HTTPException(
                    detail=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response.raise_for_status()

            return SandboxUpiVerifyResponse.model_validate(response.json())
        except requests.RequestException as e:
            data = response.json()
            message = data.get("message", "No message found")
            logger.error("Message: %s", message)
            raise HTTPException(detail=message, status_code=response.status_code) from e
        except HTTPException as err:
            raise err
        except Exception as e:
            logger.error("Failed to verify UPI: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        finally:
            response.close()


# Usage
# sandbox = Sandbox()
# sandbox.authenticate()
# sandbox.refresh_token()
