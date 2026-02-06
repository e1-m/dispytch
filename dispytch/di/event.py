from typing import Annotated


class _Event:
    # TODO: Rewrite the handler example
    """ Represents an event marker to be used as a dependency in you handler functions

    Example::

        class UserCreatedEvent(BaseModel):
            user_id: int
            timestamp: int

        @handle_group.handler(topic="user_topic", event="user_created")
        async def handle(event: Event[UserCreatedEvent]):
            print(event.body.user_id)

    """

    pass


type Event[T] = Annotated[T, _Event]
