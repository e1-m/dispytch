import asyncio
import logging

from dispytch.listener.consumer import Consumer, Message, EventSubscription
from dispytch.listener.handler import Handler, EventHandlerContext
from dispytch.listener import Router
from dispytch.listener.handler_tree import HandlerTree
from dispytch.listener.middleware import Middleware
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
            middlewares: list[Middleware] = None,
    ):
        self.consumer = consumer
        self.route_delimiter: str = route_delimiter
        self.deserializer = deserializer or JSONDeserializer()
        self._middlewares = middlewares if middlewares else []
        self._handlers: HandlerTree = HandlerTree()

        self._tasks = set()

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
        event = self.deserializer.deserialize(msg.payload)
        event_route = msg.subscription.get_path_segments(self.route_delimiter)

        handlers = self._handlers.get(event_route)

        if not handlers:
            logging.info(f'There is no handler for `{msg.subscription}`')
            return

        tasks = [asyncio.create_task(
            handler.handle(
                EventHandlerContext(
                    event=event,
                    actual_event_route=event_route,
                    subscription_pattern=subscription.get_path_segments(self.route_delimiter),
                )
            )
        ) for subscription, handler in handlers]
        await asyncio.gather(*tasks)

        await self.consumer.ack(msg)

    def handler(
            self,
            subscription: EventSubscription,
            *,
            middlewares: list[Middleware] = None,
    ):
        """
            Decorator to register a handler function for a specific topic and event type.
        """
        middlewares = middlewares if middlewares else []

        def decorator(callback):
            self._handlers.insert(
                subscription.get_path_segments(self.route_delimiter),
                (
                    subscription,
                    Handler(
                        func=callback,
                        middlewares=self._middlewares + middlewares
                    )
                )
            )
            return callback

        return decorator

    def add_handler_group(self, group: Router):
        """
        Registers ``HandlerGroup``'s handlers with the listener.

        Args:
            group (Router): A ``HandlerGroup`` object to register with the listener.
        """
        for subscription in group.get_subscriptions():
            self._handlers.insert(
                subscription.get_path_segments(self.route_delimiter),
                *[(subscription, Handler(handler_data.func, self._middlewares + handler_data.middlewares))
                  for handler_data in group.get_handlers(subscription)]
            )
