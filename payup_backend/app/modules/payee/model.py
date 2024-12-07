from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime


class PayeeModel(BaseModel):
    payee_id: UUID = Field(default_factory=uuid4)
    user_id: UUID  # Corresponding to `user_id` in the PayeeSchema
    name: str
    upi_id: Optional[str] = None  # UPI ID is optional in the schema
    bank_name: Optional[str] = None  # Optional based on your schema
    ifsc: Optional[str] = None  # IFSC code is optional in the schema
    account_number: Optional[str] = None  # Optional field for bank account number
    last_paid: Optional[datetime] = None  # Last paid is optional
    phone_number: str  # Phone number is required
    created_at: Optional[datetime] = None  # Optional, but can be auto-set
    updated_at: Optional[datetime] = None  # Optional, but can be auto-set

    class Config:
        orm_mode = True


class AddPayeeRequest(BaseModel):
    upi_id: Optional[str] = None  # UPI ID is optional in the schema
    ifsc: Optional[str] = None  # IFSC code is optional in the schema
    account_number: Optional[str] = None  # Optional field for bank account number
    phone_number: str  # Phone number is required
    pan_number: str  # PAN number is optional
    bank_name: Optional[str] = None


class DeletePayeeRequest(BaseModel):
    payee_id: UUID
