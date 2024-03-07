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


class VerifierBase(BaseModel):
    """minimum credential information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )
    user_id: UUID4


class VerifierUpdate(VerifierBase):
    phone_verifier: Optional[int] = None
    v_id: Optional[str] = None
    m_pin: Optional[str] = None
    phone_lock: Optional[bool] = None
    phone_number: Optional[str] = None
    user_id: Optional[UUID4] = None


class CredentialUpdate(VerifierBase):
    m_pin: Optional[str] = None
    phone_lock: Optional[bool] = None
    phone_number: str


class VerifierRegister(VerifierBase):
    phone_verifier: int
    v_id: str


class VerifierCreate(VerifierRegister):
    phone_number: str
    phone_verifier: int
    v_id: str


class Verifier(VerifierCreate):
    id: UUID4


class RegisterNumberRequestBase(BaseModel):
    id_token: str
    verifier: int
    phone_number: str


class OTPRequestBase(BaseModel):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]


class OTPVerifyRequest(OTPRequestBase):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]
    otp: Annotated[int, Field(..., ge=100000, lt=1000000)]


class AuthResponse(BaseResponse):
    user_data: Optional[UserModel] = None
