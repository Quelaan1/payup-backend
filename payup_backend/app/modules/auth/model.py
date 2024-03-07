from typing import Optional
from pydantic import BaseModel

from ..user.model import User as UserModel
from ...models.py_models import BaseResponse
from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict, SecretStr


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
    phone_number: str


class OTPVerifyRequest(OTPRequestBase):
    otp: int


class AuthResponse(BaseResponse):
    user_data: Optional[UserModel] = None
