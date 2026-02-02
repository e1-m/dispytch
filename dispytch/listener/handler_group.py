import random
from collections import defaultdict
from typing import Callable, Sequence

from dispytch.listener.handler import Handler
from dispytch.listener.consumer import EventSubscription


class HandlerGroup:
    def __init__(self):
        self._handlers: dict[EventSubscription, list[Handler]] = defaultdict(list)

    def handler(
            self,
            subscription: EventSubscription,
            *,
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
            handlers = self._handlers[subscription]

            handlers.append(Handler(callback, subscription, retries, retry_on, base_delay_sec, max_delay_sec, jitter))
            return callback

        return decorator

    def get_handlers(self, subscription: EventSubscription):
        return self._handlers[subscription]

    def get_subscriptions(self) -> list[EventSubscription]:
        return list(self._handlers.keys())
