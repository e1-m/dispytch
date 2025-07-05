from dataclasses import dataclass


@dataclass
class Event[Body]:
    """ Represents an event to be used as a dependency in you handler functions
    This class is generic, allowing for schema-on-read validation using typed payloads.

    Example::

        class UserCreatedEvent(BaseModel):
            user_id: int
            timestamp: int

        @handle_group.handler(topic="user_topic", event="user_created")
        async def handle(event: Event[UserCreatedEvent]):
            print(event.body.user_id)

    """

    id: str
    topic: str
    type: str
    body: Body


@dataclass
class EventHandlerContext:
    event: dict
