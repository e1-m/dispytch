from dispytch.emitter.event import EventBase
from dispytch.emitter.producer import Producer


class EventEmitter:
    """
    Used for sending events using the provided producer.

    Wraps a low-level producer and emits structured EventBase instances
    to the appropriate topic with metadata and payload.

    Args:
        producer (Producer): The message producer responsible for sending events.
    """

    def __init__(self, producer: Producer):
        self.producer = producer

    async def emit(self, event: EventBase):
        await self.producer.send(
            topic=event.__topic__,
            payload={
                'id': event.id,
                'type': event.__event_type__,
                'body': event.model_dump(exclude={'id'})
            },
            config=event.__backend_config__
        )
