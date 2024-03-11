"""application auth validation models"""

from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints, Field
from datetime import datetime
from ..user.model import User as UserModel
from ...models.py_models import BaseResponse
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict, SecretStr

from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict, SecretStr
from ..profile.model import Profile


class OTPBase(BaseModel):
    """minimum otp information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class OTPUpdate(OTPBase):
    """otp update model to pass to dao"""

    m_otp: int
    expires_at: datetime = datetime.now()


class OTPCreate(OTPUpdate):
    """otp create model to be passed to otp_dao"""

    id: UUID4


class OTP(OTPBase):
    """otp model returned from otp_dao"""

    id: UUID4
    m_otp: int
    expires_at: datetime


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


class OTPVerifyResponse(BaseResponse, Profile):
    """response on successful otp sent"""


class OTPVerifyRequest(OTPRequestBase):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]
    otp: Annotated[int, Field(..., ge=100000, lt=1000000)]


class AuthResponse(BaseResponse):
    user_data: Optional[UserModel] = None
