from typing import Union, Optional
from pydantic import BaseModel, Field


class UpiVerifyRequest(BaseModel):
    vpa: str = Field(..., description="Virtual payment address to verify")


class UpiVerifyResponse(BaseModel):
    valid: bool = Field(..., description="True if the provided VPA is valid")
    name: Optional[str] = Field(
        None, description="Name of the virtual payment address holder"
    )
    message: Optional[str] = Field(None, description="Error message for invalid VPA")


class AttestError(BaseModel):
    code: int = Field(..., description="Unique error code")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error message")


class PanVerifyRequest(BaseModel):
    pan: str = Field(..., description="PAN number to verify")


class PanVerifyResponse(BaseModel):
    valid: bool = Field(..., description="True if the provided PAN is valid")
    category: Optional[str] = Field(None, description="Category of the tax payer")
    name: Optional[str] = Field(None, description="Registered name of the PAN holder")
    displayName: Optional[str] = Field(
        None, description="Name as displayed on the PAN card"
    )
    gender: Optional[str] = Field(None, description="Gender of the individual")
    birthOrIncorporatedDate: Optional[str] = Field(
        None, description="Date of birth or incorporation"
    )
    aadhaarLinked: Optional[bool] = Field(
        None, description="Flag indicating whether PAN is linked to Aadhaar"
    )
    maskedAadhaar: Optional[str] = Field(
        None, description="Masked last 4 digits of Aadhaar number"
    )
    state: Optional[str] = Field(None, description="State name of the address location")
    city: Optional[str] = Field(None, description="City name of the address location")
    zip: Optional[Union[str, int]] = Field(
        None, description="Pin code of the address location"
    )
    country: Optional[str] = Field(None, description="Country name")
    address: Optional[str] = Field(
        None, description="Complete address of the individual or business"
    )
    message: Optional[str] = Field(None, description="Error message for invalid PAN")


class IFSCDetails(BaseModel):
    valid: bool = Field(..., description="True if the IFSC code is valid")
    bank: str = Field(..., description="Name of the bank")
    code: str = Field(..., description="Bank code")
    ifsc: str = Field(..., description="IFSC code")
    micr: Optional[str] = Field(None, description="MICR code")
    branch: str = Field(..., description="Branch name")
    city: str = Field(..., description="City name")
    district: str = Field(..., description="District name")
    state: str = Field(..., description="State name")
    address: str = Field(..., description="Complete branch address")
    neft: bool = Field(..., description="NEFT availability")
    imps: bool = Field(..., description="IMPS availability")
    rtgs: bool = Field(..., description="RTGS availability")


class BankVerifyRequest(BaseModel):
    acc: str = Field(..., description="Account number to verify")
    ifsc: str = Field(..., description="IFSC code to verify")
    fetchIfsc: bool = Field(
        False, description="Flag to fetch IFSC details if account is valid"
    )


class BankVerifyResponse(BaseModel):
    valid: bool = Field(
        ..., description="True if the provided account and IFSC combination is valid"
    )
    name: Optional[str] = Field(
        None, description="Name of the account holder as per bank records"
    )
    message: Optional[str] = Field(
        None, description="Message if account/IFSC is invalid"
    )
    suggestion: Optional[str] = Field(
        None, description="Suggested new IFSC codes after bank mergers"
    )
    status: str = Field(
        ...,
        description="Status code describing the account status",
        # Possible values: ACTIVE, INVALID, BLOCKED, CLOSED, NRE, INVALID_IFSC
    )
    ifsc: Optional[IFSCDetails] = Field(
        None, description="IFSC details when fetchIfsc is true"
    )
