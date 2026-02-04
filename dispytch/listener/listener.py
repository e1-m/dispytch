import asyncio
import logging

from dispytch.di.context import DIContext
from dispytch.di.solver import DIResolver
from dispytch.listener.consumer import Consumer, Message, EventSubscription
from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.handler import Handler
from dispytch.listener.handler_group import HandlerGroup
from dispytch.listener.handler_tree import HandlerTree
from dispytch.listener.retry import RetryPolicy
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
            default_retry_policy: RetryPolicy = None,
    ):
        self.consumer = consumer
        self.route_delimiter: str = route_delimiter
        self.deserializer = deserializer or JSONDeserializer()
        self.default_dlh = default_dlh
        self.default_retry_policy = default_retry_policy
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
        event = self.deserializer.deserialize(msg.payload).model_dump()
        event_route = msg.subscription.get_path_segments(self.route_delimiter)

        handlers = self._handlers.get(event_route)

        if not handlers:
            logging.info(f'There is no handler for `{msg.subscription}`')
            return

        tasks = [asyncio.create_task(
            handler.handle(
                DIResolver(
                    DIContext(
                        event=event,
                        actual_event_route=event_route,
                        subscription_pattern=handler.subscription.get_path_segments(self.route_delimiter),
                    )
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
            retry_policy: RetryPolicy = None,
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
                    retry_policy=retry_policy or self.default_retry_policy,
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
