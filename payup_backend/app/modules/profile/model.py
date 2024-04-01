"""application profile validation models"""

from typing import Optional, Annotated
from pydantic import BaseModel, UUID4, Field, ConfigDict, EmailStr


class ProfileBase(BaseModel):
    """minimum profile information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class ProfileUpdateRequest(ProfileBase):
    """profile update request model"""

    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileUpdate(ProfileUpdateRequest):
    """profile update request model"""

    kyc_pan: Optional[bool] = None
    kyc_uidai: Optional[bool] = None
    kyc_complete: Optional[bool] = None


class ProfileCreate(ProfileUpdate):
    """profile create model to be passed to profile_dao"""


class Profile(ProfileBase):
    """profile model returned from profile_dao"""

    id: UUID4 = Field()
    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarded: bool
    kyc_complete: bool
    kyc_pan: bool
    kyc_uidai: bool
