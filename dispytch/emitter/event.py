import uuid
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    """
    Base class for defining events.

    Attributes:
        __topic__ (str): The topic to which this event should be published.
        __event_type__ (str): An identifier for the type of event.

        __partition_by__ (Optional[str]):
            Name of an attribute to use for deciding which partition this event should be sent to (Kafka-specific).

    Example::

        class User(BaseModel):
            id: str
            email: str
            name: str

        class UserCreatedEvent(EventBase):
            __topic__ = "user_events"
            __event_type__ = "user_registered"

            __partition_by__ = "user.id'

            user: User
            timestamp: int
    """
    __topic__: ClassVar[str]
    __event_type__: ClassVar[str]

    # kafka-specific
    __partition_by__: ClassVar[Optional[str]] = None

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
