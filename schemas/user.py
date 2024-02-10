from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    email: str
    password: str


class User(UserBase):
    id: int
    email: str

    class Config:
        orm_mode = True
