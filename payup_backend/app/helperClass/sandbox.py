"""interface to sandbox api"""

import requests
from ..modules.kyc.pan.pan_model import SandboxPANVerifyResponse


class Sandbox:

    def __init__(self, sandbox_api_key: str, sandbox_secret: str):
        self.api_key = sandbox_api_key
        self.api_secret = sandbox_secret
        self.access_token = None
        self.token_expiry = None

    def authenticate(self):
        if self.api_key is None or self.api_secret is None:
            print("API key or secret not found in environment variables.")
            return

        url = "https://api.sandbox.co.in/authenticate"
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "x-api-version": "1.0",
        }

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
        except requests.RequestException as e:
            print(f"Failed to authenticate: {e}")

    def refresh_token(self):
        if self.access_token is None:
            print("Failed to refresh token as authentication failed")
            return

        url = "https://api.sandbox.co.in/authorize"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
        }

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
        except requests.RequestException as e:
            print(f"Failed to refresh token: {e}")

    def verifyPan(self, pan_number):
        if not self.access_token:
            self.access_token()
            if not self.access_token:
                print("Cannot verify PAN as authentication failed")
                return

        url = f"https://api.sandbox.co.in/pans/{pan_number}/verify?consent=y&reason=For%20KYC%20of%20User"
        headers = {
            "accept": "application/json",
            "Authorization": self.access_token,
            "x-api-key": self.api_key,
            "x-api-version": "1.0",
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 401:  # Unauthorized or token expired
                self.refresh_token()
                headers["Authorization"] = self.access_token
                response = requests.get(url, headers=headers)

            response.raise_for_status()
            res = SandboxPANVerifyResponse.model_validate_json(response.json())
            return res
        except requests.RequestException as e:
            print(f"Failed to verify PAN: {e}")
            return None


# Usage
# sandbox = Sandbox()
# sandbox.authenticate()
# sandbox.refresh_token()
