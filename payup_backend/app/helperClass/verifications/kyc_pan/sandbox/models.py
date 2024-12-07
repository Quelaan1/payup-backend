from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PANVerifiedUserData(BaseModel):
    """user data received from sandbox pan-verification api"""

    Entity: str = Field(..., alias="@entity")
    Pan: str = Field(..., alias="pan")
    # FullName: str = Field(..., alias="full_name")
    MatchName: bool = Field(..., alias="name_as_per_pan_match")
    MatchDob: bool = Field(..., alias="date_of_birth_match")
    Status: str = Field(..., alias="status")
    Category: str = Field(..., alias="category")
    AadhaarSeedingStatus: str = Field(..., alias="aadhaar_seeding_status")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="ignore"
    )


class SandboxPANVerifyData(BaseModel):
    """request data for sandbox pan-verification api"""

    Entity: str = Field("in.co.sandbox.kyc.pan_verification.request", alias="@entity")
    Pan: str = Field(..., alias="pan")
    NameAsPerPan: str = Field(..., alias="name_as_per_pan")
    DateOfBirth: str = Field(..., alias="date_of_birth")
    Consent: str = Field("n", alias="consent")
    Reason: str = Field("for onboarding customers", alias="reason")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SandboxPANVerifyResponse(BaseModel):
    """response from sandbox pan-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[PANVerifiedUserData] = Field(None, alias="data")
    Message: Optional[str] = Field(None, alias="message")
    Timestamp: int = Field(..., alias="timestamp")
    TransactionId: str = Field(..., alias="transaction_id")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OtpData(BaseModel):
    """user data received from sandbox pan-verification api"""

    RefId: Optional[str] = Field(None, alias="ref_id")
    Message: Optional[str] = Field(None, alias="message")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SandboxAadhaarOtpResponse(BaseModel):
    """response from sandbox pan-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[OtpData] = Field(None, alias="data")
    Message: Optional[str] = Field(None, alias="message")
    Timestamp: Optional[int] = Field(None, alias="timestamp")
    TransactionId: str = Field(..., alias="transaction_id")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="ignore"
    )


class SplitAddressModel(BaseModel):
    """address data received from sandbox aadhaarn-verification api"""

    Country: Optional[str] = Field(None, alias="country")
    Street: Optional[str] = Field(None, alias="street")
    Dist: Optional[str] = Field(None, alias="dist")
    House: Optional[str] = Field(None, alias="house")
    Landmark: Optional[str] = Field(None, alias="landmark")
    Pincode: Optional[str] = Field(None, alias="pincode")
    Po: Optional[str] = Field(None, alias="po")
    State: Optional[str] = Field(None, alias="state")
    Street: Optional[str] = Field(None, alias="street")
    Vtc: Optional[str] = Field(None, alias="vtc")
    Subdist: Optional[str] = Field(None, alias="subdist")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="ignore"
    )


class AadhaarData(BaseModel):
    """user data received from sandbox aadhaarn-verification api"""

    RefId: Optional[str] = Field(None, alias="ref_id")
    Message: Optional[str] = Field(None, alias="message")
    CareOf: Optional[str] = Field(None, alias="care_of")
    Status: Optional[str] = Field(None, alias="status")
    Address: Optional[str] = Field(None, alias="address")
    DOB: Optional[str] = Field(None, alias="dob")
    Email: Optional[str] = Field(None, alias="email")
    Gender: Optional[str] = Field(None, alias="gender")
    Name: Optional[str] = Field(None, alias="name")
    YearOfBirth: Optional[str] = Field(None, alias="year_of_birth")
    # MobileHash: Optional[str] = Field(None, alias="mobile_hash")
    # PhotoLink: Optional[str] = Field(None, alias="photo_link")
    SplitAddress: Optional[SplitAddressModel] = Field(None, alias="split_address")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="ignore"
    )


class SandboxAadhaarVerifyResponse(BaseModel):
    """response from sandbox aadhaar-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[AadhaarData] = Field(None, alias="data")
    Message: Optional[str] = Field(None, alias="message")
    Timestamp: int = Field(..., alias="timestamp")
    TransactionId: str = Field(..., alias="transaction_id")

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="ignore"
    )


class UpiData(BaseModel):
    """user data received from sandbox upi-verification api"""

    AccountExists: bool = Field(..., alias="account_exists")
    NameAtBank: Optional[str] = Field(None, alias="name_at_bank")


class SandboxUpiVerifyResponse(BaseModel):
    """response from sandbox upi-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[UpiData] = Field(None, alias="data")
    Message: Optional[str] = Field(None, alias="message")
    Timestamp: int = Field(..., alias="timestamp")
    TransactionId: str = Field(..., alias="transaction_id")
