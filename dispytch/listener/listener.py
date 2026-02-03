import asyncio
import logging
import random
from typing import Sequence, Callable

from dispytch.di.event import Event
from dispytch.di.context import EventHandlerContext
from dispytch.listener.consumer import Consumer, Message, EventSubscription
from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.handler import Handler
from dispytch.listener.handler_group import HandlerGroup
from dispytch.listener.handler_tree import HandlerTree
from dispytch.serialization import Deserializer
from dispytch.serialization.json import JSONDeserializer


class EventListener:
    """
    Coordinates the dispatch of consumed events to their corresponding handlers.

    Listens to an async event stream from the provided consumer and routes each event
    to the appropriate handler(s) based on topic and event type.

    """

    def __init__(
            self,
            consumer: Consumer,
            route_delimiter: str = None,
            deserializer: Deserializer = None,
            default_dlh: DeadLetterHandler = None,
    ):
        self.consumer = consumer
        self.route_delimiter: str = route_delimiter
        self.deserializer = deserializer or JSONDeserializer()
        self.default_dlh = default_dlh
        self._tasks = set()
        self._handlers: HandlerTree = HandlerTree()

    async def listen(self):
        """
        Starts an async loop that consumes events and dispatches them to registered handlers.
        """

        async for message in self.consumer.listen():
            task = asyncio.create_task(self._handle_message(message))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        if self._tasks:
            await asyncio.wait(self._tasks)

    async def _handle_message(self, msg: Message):
        event = Event(
            **self.deserializer.deserialize(msg.payload).model_dump()
        )

        handlers = self._handlers.get(
            msg.subscription.get_path_segments(self.route_delimiter)
        )

        if not handlers:
            logging.info(f'There is no handler for `{msg.subscription}`')
            return

        tasks = [asyncio.create_task(
            handler.handle(
                EventHandlerContext(
                    event=event,
                    actual_event_route=msg.subscription.get_path_segments(self.route_delimiter),
                    subscription_pattern=handler.subscription.get_path_segments(self.route_delimiter),
                )
            )
        ) for handler in handlers]
        await asyncio.gather(*tasks)

        await self.consumer.ack(msg)

    def handler(
            self,
            subscription: EventSubscription,
            *,
            dlh: DeadLetterHandler = None,
            retries: int = 0,
            retry_on: Sequence[type[Exception]] | None = None,
            base_delay_sec: float = 1.0,
            max_delay_sec: float = 30.0,
            jitter: Callable[[float], float] = lambda t: random.uniform(0, t)
    ):
        """
            Decorator to register a handler function for a specific topic and event type.
        """

        def decorator(callback):
            self._handlers.insert(
                subscription.get_path_segments(self.route_delimiter),
                Handler(
                    func=callback,
                    subscription=subscription,
                    dlh=dlh or self.default_dlh,
                    retries=retries,
                    retry_on=retry_on,
                    base_delay_sec=base_delay_sec,
                    max_delay_sec=max_delay_sec,
                    jitter=jitter
                )
            )
            return callback

        return decorator

    def add_handler_group(self, group: HandlerGroup):
        """
        Registers ``HandlerGroup``'s handlers with the listener.

        Args:
            group (HandlerGroup): A ``HandlerGroup`` object to register with the listener.
        """
        for subscription in group.get_subscriptions():
            self._handlers.insert(
                subscription.get_path_segments(self.route_delimiter),
                *group.get_handlers(subscription)
            )
