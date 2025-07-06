import logging
from inspect import isawaitable
from typing import Callable

from dispytch.emitter.event import EventBase
from dispytch.emitter.producer import Producer, ProducerTimeout

logger = logging.getLogger(__name__)


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
        self.on_timeout = lambda e: logger.warning(f"Event {e} hit a timeout during emission")

    async def emit(self, event: EventBase):
        try:
            await self.producer.send(
                topic=event.__topic__,
                payload={
                    'id': event.id,
                    'type': event.__event_type__,
                    'body': event.model_dump(exclude={'id'})
                },
                config=event.__backend_config__
            )
        except ProducerTimeout:
            if isawaitable(res := self.on_timeout(event)):
                await res

    def on_timeout(self, callback: Callable[[EventBase], None]):
        self.on_timeout = callback
        return callback
