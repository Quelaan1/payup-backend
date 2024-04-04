"""application auth validation models"""

from typing import Annotated, Union
from typing_extensions import Doc
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict
from fastapi.param_functions import Form

from ...models.py_models import BaseResponse
from ..profile.model import Profile
from ..token.model import TokenBody


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


class OTPVerifyResponse(BaseResponse, TokenBody):
    """response on successful otp sent"""

    user_data: Profile
    # token_data: TokenBody


class OTPVerifyRequest(OTPRequestBase):
    phone_number: Annotated[
        str,
        Field(..., pattern=r"^\d{10}$"),
    ]
    otp: Annotated[int, Field(..., ge=100000, lt=1000000)]


class AuthResponse(BaseResponse, TokenBody):
    profile_id: UUID4

    # user_data: Profile
    # token_data: TokenBody


class OAuth2PinRequestForm:
    """
    fasfdsf
    """

    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="password"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". Nevertheless, this dependency class is permissive and
                allows not passing it. If you want to enforce it, use instead the
                `OAuth2PasswordRequestFormStrict` dependency.
                """
            ),
        ] = None,
        phone_number: Annotated[
            str,
            Form(),
            Doc(
                """
                `phonenumber` string. The OAuth2 spec requires the exact field name
                `phonenumber`.
                """
            ),
        ],
        pin: Annotated[
            str,
            Form(),
            Doc(
                """
                `pin` string. The OAuth2 spec requires the exact field name
                `pin".
                """
            ),
        ],
    ):
        self.grant_type = grant_type
        self.phone_number = phone_number
        self.pin = pin
