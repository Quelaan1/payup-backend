from typing import Optional
from pydantic import BaseModel, Field


class PANVerifyRequestSchema(BaseModel):
    pan_number: str


class PANVerifyResponseSchema(BaseModel):
    message: str


class PANVerifiedUserData(BaseModel):
    """user data received from sandbox pan-verification api"""

    Entity: str = Field(..., alias="@entity")
    Pan: str = Field(..., alias="pan")
    FullName: str = Field(..., alias="full_name")
    Status: str = Field(..., alias="status")
    Category: str = Field(..., alias="category")

    class Config:
        populate_by_name = True
        orm_mode = True


class SandboxPANVerifyResponse(BaseModel):
    """response from sandbox pan-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[PANVerifiedUserData] = Field(..., alias="data")
    Message: Optional[str] = Field(..., alias="message")
    Timestamp: int = Field(..., alias="timestamp")
    TransactionId: int = Field(..., alias="transaction_id")

    class Config:
        populate_by_name = True
        orm_mode = True
