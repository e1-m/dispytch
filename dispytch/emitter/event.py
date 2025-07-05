import uuid
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    __topic__: ClassVar[str]
    __event_type__: ClassVar[str]

    # kafka-specific
    __partition_by__: ClassVar[Optional[str]] = None

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
