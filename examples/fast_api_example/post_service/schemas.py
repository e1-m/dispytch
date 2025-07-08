from pydantic import BaseModel


class PostIn(BaseModel):
    title: str
    content: str


class PostOut(BaseModel):
    title: str
    content: str
