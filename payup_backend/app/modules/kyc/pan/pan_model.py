from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PANVerifyRequestSchema(BaseModel):
    pan_number: str
    name: str
    consent: str
    dob: str


class PANVerifyResponseSchema(BaseModel):
    message: str
    name: Optional[str] = None


class AadhaarOtpRequestSchema(BaseModel):
    aadhaar_number: str = Field(..., max_length=12, min_length=12, pattern=r"^\d{12}$")


class AadhaarVerifyRequestSchema(BaseModel):
    otp: str
    ref_id: str
