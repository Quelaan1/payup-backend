"""application user validation models"""

from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict

from ...cockroach_sql.db_enums import UserType


class UserBase(BaseModel):
    """minimum user information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
        use_enum_values=True,
    )


class UserUpdate(UserBase):
    """user update model to pass to dao"""

    phone_lock: Optional[bool] = None
    is_active: Optional[bool] = None


class UserCreate(UserUpdate):
    """user create model to be passed to user_dao"""

    user_type: UserType
    profile_id: UUID4


class User(UserBase):
    """user model returned from user_dao"""

    id: UUID4
    is_active: bool
    phone_lock: bool
    user_type: int
    profile_id: UUID4
