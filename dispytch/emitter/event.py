import uuid
from typing import ClassVar

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    __topic__: ClassVar[str]
    __event_type__: ClassVar[str]

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
