import random
from collections import defaultdict
from typing import Callable, Sequence

from dispytch.listener.dlq import DeadLetterHandler
from dispytch.listener.handler import Handler
from dispytch.listener.consumer import EventSubscription
from dispytch.listener.retry import RetryPolicy


class HandlerGroup:
    def __init__(
            self,
            default_dlh: DeadLetterHandler = None,
            default_retry_policy: RetryPolicy = None,
    ):
        self.default_dlh = default_dlh
        self.default_retry_policy = default_retry_policy

        self._handlers: dict[EventSubscription, list[Handler]] = defaultdict(list)

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
            handlers = self._handlers[subscription]

            handlers.append(
                Handler(
                    func=callback,
                    subscription=subscription,
                    dlh=dlh or self.default_dlh,
                    retry_policy=retry_policy or self.default_retry_policy,
                )
            )
            return callback

        return decorator

    def get_handlers(self, subscription: EventSubscription):
        return self._handlers[subscription]

    def get_subscriptions(self) -> list[EventSubscription]:
        return list(self._handlers.keys())
