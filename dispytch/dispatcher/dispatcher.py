import asyncio
import logging

from dispytch.dispatcher.ack_policy import AckPolicy, AckAfterProcessing
from dispytch.dispatcher.consumer import Consumer, Message
from dispytch.dispatcher.consumer import EventSubscription
from dispytch.dispatcher.handler import Middleware, Handler, EventHandlerContext
from dispytch.dispatcher.router import Router
from dispytch.dispatcher.trie import Trie
from dispytch.serialization import Deserializer
from dispytch.serialization.json import JSONDeserializer

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Coordinates the dispatch of consumed events to their corresponding handlers.

    Listens to an async event stream from the provided consumer and routes each event
    to the appropriate handler(s) based on subscription.

    """

    def __init__(
            self,
            consumer: Consumer,
            route_delimiter: str = None,
            deserializer: Deserializer = None,
            default_ack_policy: AckPolicy = None,
            middlewares: list[Middleware] = None,
    ):
        self.consumer = consumer
        self.route_delimiter: str = route_delimiter
        self.deserializer = deserializer or JSONDeserializer()
        self.default_ack_policy = default_ack_policy or AckAfterProcessing()
        self._middlewares = middlewares if middlewares else []
        self._handlers: Trie[tuple[EventSubscription, Handler]] = Trie()
        self._ack_policies: Trie[AckPolicy] = Trie()

        self._tasks = set()

    async def start(self):
        """
        Starts an async loop that consumes events and dispatches them to registered handlers.
        """

        def handle_result(t):
            self._tasks.discard(t)

            exceptions = [res for res in t.result() if isinstance(res, Exception)]

            for exc in exceptions:
                logger.error(f"Handler failed with error: {exc}", exc_info=exc)

        async for message in self.consumer.listen():
            task = asyncio.create_task(
                self._handle_message(message)
            )
            self._tasks.add(task)
            task.add_done_callback(handle_result)

        if self._tasks:
            done, pending = await asyncio.wait(self._tasks, timeout=30.0)

            if pending:
                logger.warning(f"Shutting down with {len(pending)} tasks still active.")

    async def _handle_message(self, msg: Message):
        event = self.deserializer.deserialize(msg.payload)
        event_route = msg.subscription.get_route_segments(self.route_delimiter)

        handlers = self._handlers.get(event_route)
        policies = self._ack_policies.get(event_route)
        ack_policy = policies[0] if len(policies) > 0 else self.default_ack_policy

        if not handlers:
            logger.warning(f'There is no registered handler for subscription: `{msg.subscription}`')
            return

        tasks = [asyncio.create_task(
            handler.handle(
                EventHandlerContext(
                    event=event,
                    actual_event_route=event_route,
                    subscription_pattern=subscription.get_route_segments(self.route_delimiter),
                )
            )
        ) for subscription, handler in handlers]

        return await ack_policy.execute(
            lambda: self.consumer.ack(msg),
            lambda: asyncio.gather(*tasks, return_exceptions=True),
        )

    def handler(
            self,
            subscription: EventSubscription,
            *,
            middlewares: list[Middleware] = None,
    ):
        """
            Decorator to register a handler function for a subscription.
        """
        middlewares = middlewares if middlewares else []

        def decorator(callback):
            self._handlers.insert(
                subscription.get_route_segments(self.route_delimiter),
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

    def add_router(self, router: Router):
        """
        Registers ``Router``'s handlers with the listener.

        Args:
            router (Router): A ``Router`` object to register with the listener.
        """
        for subscription in router.get_subscriptions():
            for handler_data in router.get_handlers(subscription):
                self._handlers.insert(
                    subscription.get_route_segments(self.route_delimiter),
                    (subscription, Handler(handler_data.func, self._middlewares + handler_data.middlewares))
                )

    def set_ack_policy(self, subscription: EventSubscription, policy: AckPolicy):
        self._ack_policies.insert(
            subscription.get_route_segments(self.route_delimiter),
            policy
        )
