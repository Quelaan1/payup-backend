from typing import Optional
from pydantic import BaseModel

from ..user.model import User as UserModel


class OTPRequestBase(BaseModel):
    phone_number: str


class OTPResponse(BaseModel):
    message: str


class OTPVerifyRequest(OTPRequestBase):
    otp: int


class OTPVerifyResponse(BaseModel):
    is_successful: bool
    message: Optional[str] = None


class AuthResponse(BaseModel):
    is_successful: bool
    message: Optional[str] = None
    user_data: Optional[UserModel] = None
