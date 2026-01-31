from collections import defaultdict

from dispytch.listener.handler import Handler
from dispytch.listener.consumer import EventSubscription


class HandlerGroup:
    def __init__(self):
        self._handlers: dict[tuple[str, ...], list[Handler]] = defaultdict(list)

    def handler(self,
                subscription: EventSubscription,
                *,
                retries: int = 0,
                retry_on: type[Exception] = None,
                retry_interval: float = 1.25):
        """
           Decorator to register a handler function for a specific topic and event type.

           Args:
               retries (int, optional): Number of times to retry the handler on failure.
                   Defaults to 0 (no retries).
               retry_on (type[Exception], optional): Exception type to trigger retries.
                   If not set, retries will be attempted on any exception.
               retry_interval (float, optional): Delay in seconds between retries.
                   Defaults to 1.25 seconds.

           """

        def decorator(callback):
            handlers = self._handlers[subscription.get_segments()]

            handlers.append(Handler(callback, subscription, retries, retry_interval, retry_on))
            return callback

        return decorator

    def get_handlers(self, subscription: EventSubscription):
        return self._handlers[subscription.get_segments()]
