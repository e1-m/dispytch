from pydantic import BaseModel


class UserNotification(BaseModel):
    value: int
    message: str
