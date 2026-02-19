import logging
from inspect import isawaitable
from typing import Callable

from dispytch.emitter.event import EventBase
from dispytch.emitter.producer import Producer, ProducerTimeout, EventRoute
from dispytch.serialization import Serializer
from dispytch.serialization.json import JSONSerializer

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Used for sending events using the provided producer.

    Wraps a low-level producer and emits structured EventBase instances
    to the appropriate topic with metadata and payload.
    """

    def __init__(self, producer: Producer, serializer: Serializer = None) -> None:
        self.producer = producer
        self.serializer = serializer or JSONSerializer()
        self._on_timeout = lambda e: logger.warning(f"Event {e} hit a timeout during emission")

    async def emit(self, event: EventBase):
        if not isinstance(event.__route__, EventRoute):
            raise TypeError(
                f"Expected a EventRoute when using EventEmitter got {type(event.__route__).__name__}"
            )

        try:
            await self.producer.send(
                route=event.__route__.format_dynamic(**event.model_dump()),
                config=event.__backend_config__,
                payload=self.serializer.serialize(event.model_dump(mode="json", by_alias=True)),
            )
        except ProducerTimeout:
            if isawaitable(res := self._on_timeout(event)):
                await res

    def on_timeout(self, callback: Callable[[EventBase], None]):
        self._on_timeout = callback
        return callback
