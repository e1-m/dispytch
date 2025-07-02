from typing import ClassVar

from pydantic import BaseModel


class EventBase(BaseModel):
    __topic__: ClassVar[str]
    __event_type__: ClassVar[str]
