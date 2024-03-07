from typing import Optional, Annotated
from pydantic import BaseModel, UUID4, Field, ConfigDict, EmailStr, SecretStr

# from ..kyc.model import Kyc as KycModel


class UserBase(BaseModel):
    """minimum user information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class UserUpdate(UserBase):
    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserUpdate):
    pass


class User(UserBase):
    id: UUID4
    is_active: bool
    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarded: bool
    kyc_complete: bool
    # kycs: Optional[list[KycModel]] = []


# data = dict(
#     list_of_ints=["1", 2, "bad"],
#     a_float="not a float",
# )
