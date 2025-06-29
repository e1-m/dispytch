from pydantic import BaseModel


class Payload(BaseModel):
    type: str
    body: dict
