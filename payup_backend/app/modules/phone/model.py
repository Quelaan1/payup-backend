"""application phone validation models"""

from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict, SecretStr


class PhoneBase(BaseModel):
    """minimum phone information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )


class PhoneUpdate(PhoneBase):
    """phone update model to pass to dao"""

    is_primary: Optional[bool] = None
    verified: Optional[bool] = None
    m_pin: Optional[SecretStr] = None


class PhoneCreate(PhoneUpdate):
    """phone create model to be passed to phone_dao"""

    m_number: int
    user_id: UUID4


class Phone(PhoneBase):
    """phone model returned from phone_dao"""

    id: UUID4
    is_primary: bool
    verified: bool
    m_number: int
    m_pin: Optional[str]
    user_id: UUID4


class PhoneResponse(PhoneBase):
    """phone model returned from phone_dao"""

    id: UUID4
    is_primary: bool
    verified: bool
    m_number: int
    pin: bool
