from pydantic import BaseModel


class OTPRequestSchema(BaseModel):
    phone_number: str


class OTPResponseSchema(BaseModel):
    message: str


class OTPVerifyRequestSchema(BaseModel):
    phone_number: str
    otp: int


class OTPVerifyResponseSchema(BaseModel):
    message: str
