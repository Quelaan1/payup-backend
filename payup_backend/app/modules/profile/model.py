"""application profile validation models"""

from typing import Optional, Annotated, Any
from pydantic import BaseModel, UUID4, Field, ConfigDict, EmailStr, model_validator


class ProfileBase(BaseModel):
    """minimum profile information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class ProfileUpdateRequest(ProfileBase):
    """profile update request model"""

    email: Annotated[
        Optional[EmailStr], Field(None, examples=list("dummy@email.com"))
    ] = None
    name: Optional[str] = None

    # @model_validator(mode="before")
    # @classmethod
    # def check_single_word(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         for k, v in data.items():
    #             if v is not None and isinstance(v, str):
    #                 v = " ".join(v.split())  # Removes extra spaces
    #                 if " " in v:
    #                     raise ValueError(f"The {k} must be without spaces.")
    #                 data[k] = v
    #     return data


class ProfileUpdate(ProfileUpdateRequest):
    """profile update request model"""

    kyc_pan: Optional[bool] = None
    kyc_uidai: Optional[bool] = None
    kyc_complete: Optional[bool] = None
    onboarded: Optional[bool] = None


class ProfileCreate(ProfileUpdate):
    """profile create model to be passed to profile_dao"""


class Profile(ProfileBase):
    """profile model returned from profile_dao"""

    id: UUID4 = Field()
    email: Annotated[Optional[EmailStr], Field(None, examples=list("dummy@email.com"))]
    name: Optional[str] = None
    onboarded: bool
    kyc_complete: bool
    kyc_pan: bool
    kyc_uidai: bool


class ProfileWithUserId(BaseModel):
    user_id: UUID4
    profile: Profile
