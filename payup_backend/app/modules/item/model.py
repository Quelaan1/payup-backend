from typing import Optional
from pydantic import BaseModel, UUID4, ConfigDict

# model_config = ConfigDict(from_attributes=True)


class ItemBase(BaseModel):
    """minimum item information"""

    model_config = ConfigDict(
        from_attributes=True, revalidate_instances="always", validate_assignment=True
    )

    title: str
    description: Optional[str]


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    pass


class Item(ItemBase):
    id: UUID4
    owner_id: UUID4
