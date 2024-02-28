from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SandboxPANVerifyResponse(BaseModel):
    """response from sandbox pan-verification api"""

    Code: int = Field(..., alias="code")
    Data: Optional[PANVerifiedUserData] = Field(None, alias="data")
    Message: Optional[str] = Field(None, alias="message")
    Timestamp: int = Field(..., alias="timestamp")
    TransactionId: int = Field(..., alias="transaction_id")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
