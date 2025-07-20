from pydantic import BaseModel


class UserIn(BaseModel):
    name: str
    age: int


class UserOut(BaseModel):
    name: str
    age: int
