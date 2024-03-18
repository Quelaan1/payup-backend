"""application auth validation models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict

from ...models.py_models import BaseResponse


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
    refresh_token: str
    access_token: str


class TokenVerifyRequest(BaseModel):
    token: str
    token_type: str


class TokenVerifyResponse(BaseResponse):
    valid: bool


class TokenRefreshRequest(BaseResponse):
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
