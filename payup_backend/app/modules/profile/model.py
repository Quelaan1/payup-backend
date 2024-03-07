"""application profile validation models"""

from typing import Optional, Annotated
from pydantic import BaseModel, UUID4, Field, ConfigDict, EmailStr


class ProfileBase(BaseModel):
    """minimum profile information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class ProfileUpdate(ProfileBase):
    """profile update request model"""

    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileCreate(ProfileUpdate):
    """profile create model to be passed to profile_dao"""


class Profile(ProfileBase):
    """profile model returned from profile_dao"""

    id: UUID4 = Field()
    is_active: bool
    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarded: bool
    kyc_complete: bool
