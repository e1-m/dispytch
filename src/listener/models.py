from pydantic import BaseModel


class Event(BaseModel):
    topic: str
    type: str
    body: dict
