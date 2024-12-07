"""pydantic models for data validation and application layer communication"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """minimum response information"""

    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances="always",
        validate_assignment=True,
    )
    message: Optional[str] = None
