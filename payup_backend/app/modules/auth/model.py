"""application auth validation models"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field, UUID4, ConfigDict
from datetime import datetime

from ..user.model import User as UserModel
from ...models.py_models import BaseResponse
from ..profile.model import Profile


class OTPBase(BaseModel):
    """minimum otp information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class OTPUpdate(OTPBase):
    """otp update model to pass to dao"""

    m_otp: int
    expires_at: datetime


class OTPCreate(OTPUpdate):
    """otp create model to be passed to otp_dao"""

    id: UUID4


class OTP(OTPBase):
    """otp model returned from otp_dao"""

    id: UUID4
    m_otp: int
    expires_at: datetime


class RefreshTokenBase(BaseModel):
    """minimum refresh_token information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class RefreshTokenUpdate(RefreshTokenBase):
    """refresh_token update model to pass to dao"""

    jti: UUID4
    expires_on: datetime


class RefreshTokenCreate(RefreshTokenUpdate):
    """refresh_token create model to be passed to refresh_token_dao
    id will be token_family
    """

    user_id: UUID4


class RefreshToken(RefreshTokenBase):
    """refresh_token model returned from refresh_token_dao"""

    id: UUID4
    jti: UUID4
    user_id: UUID4
    expires_on: datetime
    updated_at: datetime


class AccessTokenBlacklistBase(BaseModel):
    """minimum access_token_blacklist information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )
    id: UUID4


class AccessTokenBlacklistCreate(AccessTokenBlacklistBase):
    """access_token_blacklist create model to be passed to access_token_blacklist_dao
    id will be jti
    """

    expires_on: datetime


class AccessTokenBlacklist(AccessTokenBlacklistBase):
    """access_token_blacklist model returned from access_token_blacklist_dao"""

    expires_on: datetime
    created_at: datetime
    updated_at: datetime


class TokenBody(BaseModel):
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"


class Credential(BaseModel):
    m_pin: Annotated[int, Field(..., ge=100000, lt=1000000)]
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]


class RegisterNumberRequestBase(BaseModel):
    id_token: str
    verifier: int
    phone_number: str


class OTPRequestBase(BaseModel):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]


class OTPResponse(BaseResponse):
    """response on successful otp sent"""


class OTPVerifyResponse(BaseResponse):
    """response on successful otp sent"""

    user_data: Profile
    token_data: TokenBody


class OTPVerifyRequest(OTPRequestBase):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]
    otp: Annotated[int, Field(..., ge=100000, lt=1000000)]


class AuthResponse(BaseResponse, TokenBody):
    pass
    # user_data: Profile
    # token_data: TokenBody
