"""interface to sandbox api"""

import logging
import requests
from typing import Optional
from fastapi import HTTPException, status

from ....modules.kyc.pan.pan_model import (
    SandboxPANVerifyResponse,
    AadhaarVerifyRequestSchema,
    SandboxAadhaarVerifyResponse,
    AadhaarOtpRequestSchema,
    SandboxAadhaarOtpResponse,
)
from ....config.constants import get_settings


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
                detail="environment not set properly",
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
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(data)
            self.access_token = data.get("access_token")
            constants.SANDBOX.update_access_token(self.access_token)
        except requests.RequestException as e:
            logger.error("Failed to authenticate: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

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
            response = requests.post(url, headers=headers, timeout=10)
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
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

    async def verifyPan(self, pan_number):
        if not self.access_token:
            await self.authenticate()

            if not self.access_token:
                logger.error("Authentication failed. Cannot verify PAN.")
                raise HTTPException(
                    detail="Authentication failed. Cannot verify PAN.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        url = f"{self._base_url}/pans/{pan_number}/verify?consent=y&reason=For%20KYC%20of%20User"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code >= 400:
                logger.info(
                    "Token expired. Refreshing token...%s", str(response.content)
                )
                data = response.json()
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.get(url, headers=headers, timeout=10)

            response.raise_for_status()
            return SandboxPANVerifyResponse.model_validate(response.json())
        except requests.RequestException as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        except Exception as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

    async def otpAadhaar(self, body: AadhaarOtpRequestSchema):
        if not self.access_token:
            await self.authenticate()

            if not self.access_token:
                logger.error("Authentication failed. Cannot verify PAN.")
                raise HTTPException(
                    detail="Authentication failed. Cannot verify PAN.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

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
                    url, json=body.model_dump(), headers=headers, timeout=10
                )

            response.raise_for_status()
            return SandboxAadhaarOtpResponse.model_validate(response.json())
        except requests.RequestException as e:
            logger.error("Failed to send OTP: %s", e.args)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        except Exception as e:
            logger.error("Failed to send OTP: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

    async def verifyAadhaar(self, body: AadhaarVerifyRequestSchema):
        if not self.access_token:
            await self.authenticate()

            if not self.access_token:
                logger.error("Authentication failed. Cannot verify PAN.")
                raise HTTPException(
                    detail="Authentication failed. Cannot verify PAN.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        url = f"{self._base_url}/kyc/aadhaar/okyc/otp/verify"

        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                url, json=body.model_dump(), headers=headers, timeout=10
            )
            if response.status_code >= 400:
                logger.info("Token expired. Refreshing token...")
                data = response.json()
                code = data.get("code")
                await self.refresh_token(code)
                headers["Authorization"] = self.access_token
                response = requests.post(
                    url, json=body.model_dump(), headers=headers, timeout=10
                )
            if response.status_code == 500:
                logger.info("OTP expired.")
                raise HTTPException(
                    detail="otp expired", status_code=status.HTTP_400_BAD_REQUEST
                )

            logger.info(response.json())
            response.raise_for_status()
            return SandboxAadhaarVerifyResponse.model_validate(response.json())
        except HTTPException as err:
            raise err
        except requests.RequestException as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e
        except Exception as e:
            logger.error("Failed to verify PAN: %s", e)
            raise HTTPException(
                detail=e.args[0], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e


# Usage
# sandbox = Sandbox()
# sandbox.authenticate()
# sandbox.refresh_token()
