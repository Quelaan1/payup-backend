from pydantic import BaseModel, Field


class OTPRequestSchema(BaseModel):
    phone_number: str


class OTPResponseSchema(BaseModel):
    message: str


class OTPVerifyRequestSchema(BaseModel):
    phone_number: str
    otp: int


class OTPVerifyResponseSchema(BaseModel):
    message: str


class PANVerifyResponseSchema(BaseModel):
    Code: str = Field()


# {
#     "code": 200,
#     "data": {
#         "@entity": "pan",
#         "pan": "BINPT2390C",
#         "full_name": "GOPINATH TILAK KUMAR",
#         "status": "VALID",
#         "category": "Individual",
#     },
#     "timestamp": 1707543074824,
#     "transaction_id": "f38313b0-e2be-495a-907e-1f6b1f564aff",
# }
