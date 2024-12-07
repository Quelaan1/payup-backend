from typing import Optional
from pydantic import BaseModel


class InitiatePaymentResponse(BaseModel):
    status: int
    error_desc: Optional[str]
    data: str


class InitiatePaymentRequest(BaseModel):
    amount: float
    productinfo: str
    payment_mode: str
